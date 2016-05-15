# -*- coding: utf-8 -*-
"""The extractor class definitions.

An extractor is a class used to extract information from "raw" data.
"""

import logging

import pysigscan

from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import profiler
from plaso.lib import errors
from plaso.parsers import interface as parsers_interface
from plaso.parsers import manager as parsers_manager


class EventExtractor(object):
  """Class that implements an event extractor object.

  The event extractor extracts events from event sources.
  """

  def __init__(self, resolver_context, parser_filter_expression=None):
    """Initializes an event extractor object.

    The parser filter expression is a comma separated value string that
    denotes a list of parser names to include and/or exclude. Each entry
    can have the value of:

    * An exact match of a list of parsers, or a preset (see
      plaso/frontend/presets.py for a full list of available presets).
    * A name of a single parser (case insensitive), e.g. msiecf.
    * A glob name for a single parser, e.g. '*msie*' (case insensitive).

    Args:
      resolver_context: a resolver context (instance of dfvfs.Context).
      parser_filter_expression: optional string containing the parser filter
                                expression, where None represents all parsers
                                and plugins.
    """
    super(EventExtractor, self).__init__()
    self._file_scanner = None
    self._filestat_parser_object = None
    self._mft_parser_object = None
    self._non_sigscan_parser_names = None
    self._parser_filter_expression = parser_filter_expression
    self._parser_objects = None
    self._parsers_profiler = None
    self._resolver_context = resolver_context
    self._specification_store = None
    self._usnjrnl_parser_object = None

    self._InitializeParserObjects()

  def _CheckParserCanProcessFileEntry(self, parser_object, file_entry):
    """Determines if a parser can process a file entry.

    Args:
      file_entry: the file entry relating to the data to be hashed (instance of
                  dfvfs.FileEntry)
      parser_object: a parser object (instance of BaseParser).

    Returns:
      A boolean value that indicates a match.
    """
    for filter_object in parser_object.FILTERS:
      if filter_object.Match(file_entry):
        return True

    return False

  def _GetSignatureMatchParserNames(self, file_object):
    """Determines if a file-like object matches one of the known signatures.

    Args:
      file_object: the file-like object whose contents will be checked
                   for known signatures.

    Returns:
      A list of parser names for which the file entry matches their
      known signatures.
    """
    parser_name_list = []
    scan_state = pysigscan.scan_state()
    self._file_scanner.scan_file_object(scan_state, file_object)

    for scan_result in iter(scan_state.scan_results):
      format_specification = (
          self._specification_store.GetSpecificationBySignature(
              scan_result.identifier))

      if format_specification.identifier not in parser_name_list:
        parser_name_list.append(format_specification.identifier)

    return parser_name_list

  def _InitializeParserObjects(self):
    """Initializes the parser objects."""
    self._specification_store, non_sigscan_parser_names = (
        parsers_manager.ParsersManager.GetSpecificationStore(
            parser_filter_expression=self._parser_filter_expression))

    self._non_sigscan_parser_names = []
    for parser_name in non_sigscan_parser_names:
      if parser_name in [u'filestat', u'usnjrnl']:
        continue
      self._non_sigscan_parser_names.append(parser_name)

    self._file_scanner = parsers_manager.ParsersManager.GetScanner(
        self._specification_store)

    self._parser_objects = parsers_manager.ParsersManager.GetParserObjects(
        parser_filter_expression=self._parser_filter_expression)

    self._filestat_parser_object = self._parser_objects.get(u'filestat', None)
    if u'filestat' in self._parser_objects:
      del self._parser_objects[u'filestat']

    self._mft_parser_object = self._parser_objects.get(u'mft', None)

    self._usnjrnl_parser_object = self._parser_objects.get(u'usnjrnl', None)
    if u'usnjrnl' in self._parser_objects:
      del self._parser_objects[u'usnjrnl']

  def _ParseDataStreamWithParser(
      self, parser_mediator, parser_object, file_entry, data_stream_name=u''):
    """Parses a data stream of a file entry with a specific parser.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      parser_object: a parser object (instance of BaseParser).
      file_entry: a file entry object (instance of dfvfs.FileEntry).
      data_stream_name: optional data stream name. The default is
                        an empty string which represents the default
                        data stream.

    Raises:
      RuntimeError: if the file-like object is missing.
    """
    file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)
    if not file_object:
      raise RuntimeError(
          u'Unable to retrieve file-like object from file entry.')

    try:
      self._ParseFileEntryWithParser(
          parser_mediator, parser_object, file_entry, file_object=file_object)

    finally:
      file_object.close()

  def _ParseFileEntryWithParser(
      self, parser_mediator, parser_object, file_entry, file_object=None):
    """Parses a file entry with a specific parser.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      parser_object: a parser object (instance of BaseParser).
      file_entry: a file entry object (instance of dfvfs.FileEntry).
      file_object: optional file-like object to parse. If not set the parser
                   will use the parser mediator to open the file entry's
                   default data stream as a file-like object.

    Raises:
      TypeError: if parser object is not a supported parser type.
    """
    if not isinstance(parser_object, (
        parsers_interface.FileEntryParser, parsers_interface.FileObjectParser)):
      raise TypeError(u'Unsupported parser object type.')

    parser_mediator.ClearParserChain()

    reference_count = self._resolver_context.GetFileObjectReferenceCount(
        file_entry.path_spec)

    if self._parsers_profiler:
      self._parsers_profiler.StartTiming(parser_object.NAME)

    try:
      if isinstance(parser_object, parsers_interface.FileEntryParser):
        parser_object.Parse(parser_mediator)
      elif isinstance(parser_object, parsers_interface.FileObjectParser):
        parser_object.Parse(parser_mediator, file_object)

    # We catch IOError so we can determine the parser that generated the error.
    except (IOError, dfvfs_errors.BackEndError) as exception:
      display_name = parser_mediator.GetDisplayName(file_entry)
      logging.warning(
          u'{0:s} unable to parse file: {1:s} with error: {2:s}'.format(
              parser_object.NAME, display_name, exception))

    except errors.UnableToParseFile as exception:
      display_name = parser_mediator.GetDisplayName(file_entry)
      logging.debug(
          u'{0:s} unable to parse file: {1:s} with error: {2:s}'.format(
              parser_object.NAME, display_name, exception))

    finally:
      if self._parsers_profiler:
        self._parsers_profiler.StopTiming(parser_object.NAME)

      if reference_count != self._resolver_context.GetFileObjectReferenceCount(
          file_entry.path_spec):
        display_name = parser_mediator.GetDisplayName(file_entry)
        logging.warning((
            u'[{0:s}] did not explicitly close file-object for file: '
            u'{1:s}.').format(parser_object.NAME, display_name))

  def ParseDataStream(self, parser_mediator, file_entry, data_stream_name=u''):
    """Parses a data stream of a file entry with the enabled parsers.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_entry: a file entry object (instance of dfvfs.FileEntry).
      data_stream_name: optional data stream name. The default is
                        an empty string which represents the default
                        data stream.

    Raises:
      RuntimeError: if the file-like object or the parser object is missing.
    """
    file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)
    if not file_object:
      raise RuntimeError(
          u'Unable to retrieve file-like object from file entry.')

    try:
      parser_name_list = self._GetSignatureMatchParserNames(file_object)
      if not parser_name_list:
        parser_name_list = self._non_sigscan_parser_names

      for parser_name in parser_name_list:
        parser_object = self._parser_objects.get(parser_name, None)
        if not parser_object:
          raise RuntimeError(
              u'Parser object missing for parser: {0:s}'.format(parser_name))

        if parser_object.FILTERS:
          if not self._CheckParserCanProcessFileEntry(
              parser_object, file_entry):
            continue

        display_name = parser_mediator.GetDisplayName(file_entry)
        logging.debug((
            u'[ParseDataStream] parsing file: {0:s} with parser: '
            u'{1:s}').format(display_name, parser_name))

        self._ParseFileEntryWithParser(
            parser_mediator, parser_object, file_entry,
            file_object=file_object)

    finally:
      file_object.close()

  def ParseFileEntryMetadata(self, parser_mediator, file_entry):
    """Parses the file entry metadata e.g. file system data.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_entry: a file entry object (instance of dfvfs.FileEntry).
    """
    if self._filestat_parser_object:
      self._ParseFileEntryWithParser(
          parser_mediator, self._filestat_parser_object, file_entry)

  def ParseMetadataFile(
      self, parser_mediator, file_entry, data_stream_name=u''):
    """Parses a metadata file.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_entry: a file entry object (instance of dfvfs.FileEntry).
      data_stream_name: optional data stream name. The default is
                        an empty string which represents the default
                        data stream.
    """
    parent_path_spec = getattr(file_entry.path_spec, u'parent', None)
    filename_upper = file_entry.name.upper()
    if (self._mft_parser_object and parent_path_spec and
        filename_upper in (u'$MFT', u'$MFTMIRR') and not data_stream_name):
      self._ParseDataStreamWithParser(
          parser_mediator, self._mft_parser_object, file_entry)

    elif (self._usnjrnl_parser_object and parent_path_spec and
          filename_upper == u'$USNJRNL' and data_stream_name == u'$J'):
      # To be able to ignore the sparse data ranges the UsnJrnl parser
      # needs to read directly from the volume.
      volume_file_object = path_spec_resolver.Resolver.OpenFileObject(
          parent_path_spec, resolver_context=self._resolver_context)

      try:
        self._ParseFileEntryWithParser(
            parser_mediator, self._usnjrnl_parser_object, file_entry,
            file_object=volume_file_object)
      finally:
        volume_file_object.close()

  def ProfilingStart(self, identifier):
    """Starts the profiling.

    Args:
      identifier: a string containg the profiling identifier.

    Raises:
      ValueError: if the parsers profiler is already set.
    """
    if self._parsers_profiler:
      raise ValueError(u'Parsers profiler already set.')

    self._parsers_profiler = profiler.ParsersProfiler(identifier)

  def ProfilingStop(self):
    """Stops the profiling.

    Raises:
      ValueError: if the parsers profiler is not set.
    """
    if not self._parsers_profiler:
      raise ValueError(u'Parsers profiler not set.')

    self._parsers_profiler.Write()
