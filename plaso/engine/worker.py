# -*- coding: utf-8 -*-
"""The event extraction worker."""

import logging
import os
import re

from dfvfs.analyzer import analyzer
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

import pysigscan

from plaso.engine import collector
from plaso.engine import profiler
from plaso.engine import queue
from plaso.lib import definitions
from plaso.lib import errors
from plaso.hashers import manager as hashers_manager
from plaso.parsers import interface as parsers_interface
from plaso.parsers import manager as parsers_manager


class BaseEventExtractionWorker(queue.ItemQueueConsumer):
  """Class that defines the event extraction worker base.

  This class is designed to watch a queue for path specifications of files
  and directories (file entries) and data streams for which events need to
  be extracted.

  The event extraction worker needs to determine if a parser suitable
  for parsing a particular file entry or data stream is available. All
  extracted event objects are pushed on a storage queue for further processing.
  """

  _DEFAULT_HASH_READ_SIZE = 4096

  # TSK metadata files that need special handling.
  _METADATA_FILE_LOCATIONS_TSK = frozenset([
      # NTFS
      u'/$AttrDef',
      u'/$BadClus',
      u'/$Bitmap',
      u'/$Boot',
      u'/$Extend/$ObjId',
      u'/$Extend/$Quota',
      u'/$Extend/$Reparse',
      u'/$Extend/$RmMetadata/$Repair',
      u'/$Extend/$RmMetadata/$TxfLog/$Tops',
      u'/$Extend/$UsnJrnl',
      u'/$LogFile',
      u'/$MFT',
      u'/$MFTMirr',
      u'/$Secure',
      u'/$UpCase',
      u'/$Volume',
      # HFS+/HFSX
      u'/$ExtentsFile',
      u'/$CatalogFile',
      u'/$BadBlockFile',
      u'/$AllocationFile',
      u'/$AttributesFile',
  ])

  # TODO: make this filtering solution more generic. Also see:
  # https://github.com/log2timeline/plaso/issues/467
  _CHROME_CACHE_DATA_FILE_RE = re.compile(r'^[fF]_[0-9]{6}$')
  _FIREFOX_CACHE_DATA_FILE_RE = re.compile(r'^[0-9a-fA-F]{5}[dm][0-9]{2}$')
  _FIREFOX_CACHE2_DATA_FILE_RE = re.compile(r'^[0-9a-fA-F]{40}$')
  _FSEVENTSD_FILE_RE = re.compile(r'^[0-9a-fA-F]{16}$')

  def __init__(
      self, identifier, path_spec_queue, event_queue_producer,
      parse_error_queue_producer, parser_mediator, resolver_context=None):
    """Initializes the event extraction worker object.

    Args:
      identifier: The identifier, usually an incrementing integer.
      path_spec_queue: The path specification queue (instance of Queue).
                       This queue contains the path specifications (instances
                       of dfvfs.PathSpec) of the file entries that need
                       to be processed.
      event_queue_producer: The event object queue producer (instance of
                            ItemQueueProducer).
      parse_error_queue_producer: The parse error queue producer (instance of
                                  ItemQueueProducer).
      parser_mediator: A parser mediator object (instance of ParserMediator).
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None which will use the built in context
                        which is not multi process safe. Note that every thread
                        or process must have its own resolver context.
    """
    super(BaseEventExtractionWorker, self).__init__(path_spec_queue)
    self._compressed_stream_path_spec = None
    self._current_display_name = u''
    self._current_file_entry = None
    self._enable_debug_mode = False
    self._identifier = identifier
    self._identifier_string = u'Worker_{0:d}'.format(identifier)
    self._file_scanner = None
    self._filestat_parser_object = None
    self._hasher_names = None
    self._non_sigscan_parser_names = None
    self._open_files = False
    self._parser_mediator = parser_mediator
    self._parser_objects = None
    self._process_archive_files = False
    self._produced_number_of_path_specs = 0
    self._resolver_context = resolver_context
    self._specification_store = None
    self._usnjrnl_parser_object = None

    self._event_queue_producer = event_queue_producer
    self._parse_error_queue_producer = parse_error_queue_producer

    # Attributes that contain the current status of the worker.
    self._status = definitions.PROCESSING_STATUS_INITIALIZED

    # Attributes for profiling.
    self._enable_profiling = False
    self._memory_profiler = None
    self._parsers_profiler = None
    self._profiling_sample = 0
    self._profiling_sample_rate = 1000

  def _CanProcessFileEntryWithParser(self, file_entry, parser_object):
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

  def _CanSkipContentExtraction(self, file_entry):
    """Determines if content extraction of a file entry can be skipped.

    Args:
      file_entry: the file entry relating to the data to be hashed (instance of
                  dfvfs.FileEntry)

    Returns:
      A boolean value to indicate the content extraction can be skipped.
    """
    # TODO: make this filtering solution more generic. Also see:
    # https://github.com/log2timeline/plaso/issues/467
    location = getattr(file_entry.path_spec, u'location', None)
    if not location:
      return False

    data_stream_name = getattr(file_entry.path_spec, u'data_stream', None)
    if data_stream_name:
      return False

    file_system = file_entry.GetFileSystem()

    path_segments = file_system.SplitPath(location)

    if self._CHROME_CACHE_DATA_FILE_RE.match(path_segments[-1]):
      location_segments = path_segments[:-1]
      location_segments.append(u'index')
      location = file_system.JoinPath(location_segments)
      index_path_spec = path_spec_factory.Factory.NewPathSpec(
          file_entry.type_indicator, location=location,
          parent=file_entry.path_spec.parent)

      if file_system.FileEntryExistsByPathSpec(index_path_spec):
        # TODO: improve this check if "index" is a Chrome Cache index file.
        return True

    elif self._FIREFOX_CACHE_DATA_FILE_RE.match(path_segments[-1]):
      location_segments = path_segments[:-4]
      location_segments.append(u'_CACHE_MAP_')
      location = file_system.JoinPath(location_segments)
      cache_map_path_spec = path_spec_factory.Factory.NewPathSpec(
          file_entry.type_indicator, location=location,
          parent=file_entry.path_spec.parent)

      if file_system.FileEntryExistsByPathSpec(cache_map_path_spec):
        # TODO: improve this check if "_CACHE_MAP_" is a Firefox Cache
        # version 1 cache map file.
        return True

    elif self._FIREFOX_CACHE2_DATA_FILE_RE.match(path_segments[-1]):
      location_segments = path_segments[:-2]
      location_segments.append(u'index')
      location = file_system.JoinPath(location_segments)
      index_path_spec = path_spec_factory.Factory.NewPathSpec(
          file_entry.type_indicator, location=location,
          parent=file_entry.path_spec.parent)

      if file_system.FileEntryExistsByPathSpec(index_path_spec):
        # TODO: improve this check if "index" is a Firefox Cache version 2
        # index file.
        return True

    elif self._FSEVENTSD_FILE_RE.match(path_segments[-1]):
      if len(path_segments) == 2 and path_segments[0].lower() == u'.fseventsd':
        return True

    elif len(path_segments) == 1 and path_segments[0].lower() in (
        u'hiberfil.sys', u'pagefile.sys', u'swapfile.sys'):
      return True

    return False

  def _ConsumeItem(self, path_spec, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).

    Raises:
      QueueFull: If a queue is full.
    """
    self._ProcessPathSpec(path_spec)

    # TODO: work-around for now the compressed stream path spec
    # needs to be processed after the current path spec.
    if self._compressed_stream_path_spec:
      self._ProcessPathSpec(self._compressed_stream_path_spec)
      self._compressed_stream_path_spec = None

  def _DebugProcessPathSpec(self):
    """Callback for debugging path specification processing failures."""
    return

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

    for scan_result in scan_state.scan_results:
      format_specification = (
          self._specification_store.GetSpecificationBySignature(
              scan_result.identifier))

      if format_specification.identifier not in parser_name_list:
        parser_name_list.append(format_specification.identifier)

    return parser_name_list

  def _HashDataStream(self, file_entry, data_stream_name=u''):
    """Hashes the contents of a specific data stream of a file entry.

    The resulting digest hashes are set in the parser mediator as attributes
    that are added to produced event objects. Note that some file systems
    allow directories to have data streams, e.g. NTFS.

    Args:
      file_entry: the file entry relating to the data to be hashed (instance of
                  dfvfs.FileEntry)
      data_stream_name: optional data stream name. The default is
                        an empty string which represents the default
                        data stream.
    """
    if not self._hasher_names:
      return

    logging.debug(u'[HashDataStream] hashing file: {0:s}'.format(
        self._current_display_name))

    self._status = definitions.PROCESSING_STATUS_HASHING

    file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)
    if not file_object:
      return

    # Make sure frame.f_locals does not keep a reference to file_entry.
    file_entry = None

    try:
      digest_hashes = hashers_manager.HashersManager.HashFileObject(
          self._hasher_names, file_object,
          buffer_size=self._DEFAULT_HASH_READ_SIZE)
    finally:
      file_object.close()

    if self._enable_profiling:
      self._ProfilingSampleMemory()

    for hash_name, digest_hash_string in iter(digest_hashes.items()):
      attribute_name = u'{0:s}_hash'.format(hash_name)
      self._parser_mediator.AddEventAttribute(
          attribute_name, digest_hash_string)

      logging.debug(
          u'[HashDataStream] digest {0:s} calculated for file: {1:s}.'.format(
              digest_hash_string, self._current_display_name))

    logging.debug(
        u'[HashDataStream] completed hashing file: {0:s}'.format(
            self._current_display_name))

  def _IsMetadataFile(self, file_entry):
    """Determines if the file entry is a metadata file.

    Args:
      file_entry: a file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean value indicating if the file entry is a metadata file.
    """
    if (file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK and
        file_entry.path_spec.location in self._METADATA_FILE_LOCATIONS_TSK):
      return True

    return False

  def _ParseFileEntryWithParser(
      self, parser_object, file_entry, file_object=None):
    """Parses a file entry with a specific parser.

    Args:
      parser_object: a parser object (instance of BaseParser).
      file_entry: a file entry object (instance of dfvfs.FileEntry).
      file_object: optional file-like object to parse. If not set the parser
                   will use the parser mediator to open the file entry's
                   default data stream as a file-like object
    """
    self._parser_mediator.ClearParserChain()

    reference_count = self._resolver_context.GetFileObjectReferenceCount(
        file_entry.path_spec)

    if self._parsers_profiler:
      self._parsers_profiler.StartTiming(parser_object.NAME)

    try:
      if isinstance(parser_object, parsers_interface.FileEntryParser):
        parser_object.Parse(self._parser_mediator)
      elif isinstance(parser_object, parsers_interface.FileObjectParser):
        parser_object.Parse(self._parser_mediator, file_object)
      else:
        logging.warning(
            u'{0:s} unsupported parser type.'.format(parser_object.NAME))

    # We catch the IOError so we can determine the parser that generated
    # the error.
    except (dfvfs_errors.BackEndError, IOError) as exception:
      logging.warning(
          u'{0:s} unable to parse file: {1:s} with error: {2:s}'.format(
              parser_object.NAME, self._current_display_name, exception))

    except errors.UnableToParseFile as exception:
      logging.debug(
          u'{0:s} unable to parse file: {1:s} with error: {2:s}'.format(
              parser_object.NAME, self._current_display_name, exception))

    finally:
      if self._parsers_profiler:
        self._parsers_profiler.StopTiming(parser_object.NAME)

      if reference_count != self._resolver_context.GetFileObjectReferenceCount(
          file_entry.path_spec):
        logging.warning((
            u'[{0:s}] did not explicitly close file-object for file: '
            u'{1:s}.').format(parser_object.NAME, self._current_display_name))

  def _ProcessArchiveFile(self, file_entry):
    """Processes an archive file (file that contains file entries).

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file is an archive file.
    """
    try:
      type_indicators = analyzer.Analyzer.GetArchiveTypeIndicators(
          file_entry.path_spec, resolver_context=self._resolver_context)
    except IOError as exception:
      logging.warning((
          u'Analyzer failed to determine archive type indicators '
          u'for file: {0:s} with error: {1:s}').format(
              self._current_display_name, exception))

      # Make sure frame.f_locals does not keep a reference to file_entry.
      file_entry = None
      return False

    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return False

    if number_of_type_indicators > 1:
      logging.debug((
          u'Found multiple format type indicators: {0:s} for '
          u'archive file: {1:s}').format(
              type_indicators, self._current_display_name))

    for type_indicator in type_indicators:
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_TAR:
        archive_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/',
            parent=file_entry.path_spec)

      elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_ZIP:
        archive_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_ZIP, location=u'/',
            parent=file_entry.path_spec)

      else:
        logging.debug((
            u'Unsupported archive format type indicator: {0:s} for '
            u'archive file: {1:s}').format(
                type_indicator, self._current_display_name))

        archive_path_spec = None

      if archive_path_spec and self._process_archive_files:
        try:
          file_system = path_spec_resolver.Resolver.OpenFileSystem(
              archive_path_spec, resolver_context=self._resolver_context)

          try:
            # TODO: make sure to handle the abort here.

            # TODO: change this to pass the archive file path spec to
            # the collector process and have the collector implement a maximum
            # path spec "depth" to prevent ZIP bombs and equiv.
            file_system_collector = collector.FileSystemCollector(self._queue)
            file_system_collector.Collect(file_system, archive_path_spec)
            self._produced_number_of_path_specs += (
                file_system_collector.number_of_produced_items)

          finally:
            file_system.Close()

            # Make sure frame.f_locals does not keep a reference to file_entry.
            file_entry = None

        except IOError:
          logging.warning(u'Unable to process archive file:\n{0:s}'.format(
              self._current_display_name))

    return True

  def _ProcessCompressedStreamFile(self, file_entry):
    """Processes an compressed stream file (file that contains file entries).

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file is a compressed stream file.
    """
    try:
      type_indicators = analyzer.Analyzer.GetCompressedStreamTypeIndicators(
          file_entry.path_spec, resolver_context=self._resolver_context)
    except IOError as exception:
      logging.warning((
          u'Analyzer failed to determine compressed stream type indicators '
          u'for file: {0:s} with error: {1:s}').format(
              self._current_display_name, exception))

      # Make sure frame.f_locals does not keep a reference to file_entry.
      file_entry = None
      return False

    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return False

    if number_of_type_indicators > 1:
      logging.debug((
          u'Found multiple format type indicators: {0:s} for '
          u'compressed stream file: {1:s}').format(
              type_indicators, self._current_display_name))

    for type_indicator in type_indicators:
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_BZIP2:
        compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=dfvfs_definitions.COMPRESSION_METHOD_BZIP2,
            parent=file_entry.path_spec)

      elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_GZIP:
        compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=file_entry.path_spec)

      else:
        logging.debug((
            u'Unsupported compressed stream format type indicators: {0:s} for '
            u'compressed stream file: {1:s}').format(
                type_indicator, self._current_display_name))

        compressed_stream_path_spec = None

      if compressed_stream_path_spec:
        # TODO: disabled for now since it can cause a deadlock.
        # self._queue.PushItem(compressed_stream_path_spec)
        # self._produced_number_of_path_specs += 1

        # TODO: work-around for now the compressed stream path spec
        # needs to be processed after the current path spec.
        self._compressed_stream_path_spec = compressed_stream_path_spec

    return True

  def _ProcessDataStream(self, file_entry, data_stream_name=u''):
    """Processes a specific data stream of a file entry.

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      data_stream_name: optional data stream name. The default is
                        an empty string which represents the default
                        data stream.
    """
    file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)
    if not file_object:
      return

    try:
      parser_name_list = self._GetSignatureMatchParserNames(file_object)
      if not parser_name_list:
        parser_name_list = self._non_sigscan_parser_names

      self._status = definitions.PROCESSING_STATUS_PARSING
      for parser_name in parser_name_list:
        parser_object = self._parser_objects.get(parser_name, None)
        if not parser_object:
          logging.warning(u'No such parser: {0:s}'.format(parser_name))
          continue

        if parser_object.FILTERS:
          if not self._CanProcessFileEntryWithParser(file_entry, parser_object):
            continue

        logging.debug((
            u'[ProcessDataStream] parsing file: {0:s} with parser: '
            u'{1:s}').format(self._current_display_name, parser_name))

        self._ParseFileEntryWithParser(
            parser_object, file_entry, file_object=file_object)

    finally:
      file_object.close()

      # Make sure frame.f_locals does not keep a reference to file_entry.
      file_entry = None

  def _ProcessFileEntry(self, file_entry, data_stream_name=u''):
    """Processes a specific data stream of a file entry.

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      data_stream_name: optional data stream name. The default is
                        an empty string which represents the default
                        data stream.

    Raises:
      RuntimeError: if the parser object is missing.
    """
    self._current_file_entry = file_entry
    self._current_display_name = self._parser_mediator.GetDisplayName(
        file_entry)

    reference_count = self._resolver_context.GetFileObjectReferenceCount(
        file_entry.path_spec)

    self._parser_mediator.SetFileEntry(file_entry)

    logging.debug(u'[ProcessFileEntry] processing file entry: {0:s}'.format(
        self._current_display_name))

    try:
      if self._IsMetadataFile(file_entry):
        parent_path_spec = getattr(file_entry.path_spec, u'parent', None)
        if (self._usnjrnl_parser_object and parent_path_spec and
            file_entry.name == u'$UsnJrnl' and data_stream_name == u'$J'):

          # To be able to ignore the sparse data ranges the UsnJrnl parser
          # needs to read directly from the volume.
          volume_file_object = path_spec_resolver.Resolver.OpenFileObject(
              parent_path_spec, resolver_context=self._resolver_context)

          try:
            self._ParseFileEntryWithParser(
                self._usnjrnl_parser_object, file_entry,
                file_object=volume_file_object)
          finally:
            volume_file_object.close()

      else:
        # Not every file entry has a data stream. In such cases we want to
        # extract the metadata only.
        has_data_stream = file_entry.HasDataStream(data_stream_name)

        if has_data_stream:
          self._HashDataStream(file_entry, data_stream_name=data_stream_name)

        # We always want to use the filestat parser if set but we only want
        # to invoke it once per file entry, so we only use it if we are
        # processing the default (nameless) data stream.
        if not data_stream_name and self._filestat_parser_object:
          self._ParseFileEntryWithParser(
              self._filestat_parser_object, file_entry)

        # Determine if the content of the file entry should not be extracted.
        skip_content_extraction = self._CanSkipContentExtraction(file_entry)
        if skip_content_extraction:
          logging.info(u'Skipping content extraction of: {0:s}'.format(
              self._current_display_name))
        else:
          is_archive = False
          is_compressed_stream = False

          if file_entry.IsFile():
            is_compressed_stream = self._ProcessCompressedStreamFile(file_entry)
            if not is_compressed_stream:
              is_archive = self._ProcessArchiveFile(file_entry)

          if has_data_stream and not is_archive and not is_compressed_stream:
            self._ProcessDataStream(
                file_entry, data_stream_name=data_stream_name)

    finally:
      if reference_count != self._resolver_context.GetFileObjectReferenceCount(
          file_entry.path_spec):
        # Clean up after parsers that do not call close explicitly.
        if self._resolver_context.ForceRemoveFileObject(file_entry.path_spec):
          logging.warning(
              u'File-object not explicitly closed for file: {0:s}'.format(
                  self._current_display_name))

      # We do not clear self._current_file_entry or self._current_display_name
      # here to allow the foreman to see which file was previously processed.

      self._parser_mediator.ResetFileEntry()

      # Make sure frame.f_locals does not keep a reference to file_entry.
      file_entry = None

    if self._enable_profiling:
      self._ProfilingSampleMemory()

    logging.debug(
        u'[ProcessFileEntry] done processing file entry: {0:s}'.format(
            self._current_display_name))

  def _ProcessPathSpec(self, path_spec):
    """Processes a path specification.

    Args:
      path_spec: A path specification object (instance of dfvfs.PathSpec).
    """
    try:
      file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          path_spec, resolver_context=self._resolver_context)

      if file_entry is None:
        logging.warning(
            u'Unable to open file entry with path spec: {0:s}'.format(
                path_spec.comparable))
        return

      # Note that data stream can be set but contain None, we'll set it
      # to an empty string here.
      data_stream_name = getattr(path_spec, u'data_stream', None)
      if not data_stream_name:
        data_stream_name = u''

      self._ProcessFileEntry(file_entry, data_stream_name=data_stream_name)

    except IOError as exception:
      logging.warning(
          u'Unable to process path spec: {0:s} with error: {1:s}'.format(
              path_spec.comparable, exception))

    except dfvfs_errors.CacheFullError:
      # TODO: signal engine of failure.
      self._abort = True
      logging.error((
          u'ABORT: detected cache full error while processing '
          u'path spec: {0:s}').format(path_spec.comparable))

    # All exceptions need to be caught here to prevent the worker
    # form being killed by an uncaught exception.
    except Exception as exception:
      logging.warning(
          u'Unhandled exception while processing path spec: {0:s}.'.format(
              path_spec.comparable))
      logging.exception(exception)

      if self._enable_debug_mode:
        self._DebugProcessPathSpec()

    # Make sure frame.f_locals does not keep a reference to file_entry.
    file_entry = None

  def _ProfilingSampleMemory(self):
    """Create a memory profiling sample."""
    if not self._memory_profiler:
      return

    self._profiling_sample += 1

    if self._profiling_sample >= self._profiling_sample_rate:
      self._memory_profiler.Sample()
      self._profiling_sample = 0

  def _ProfilingStart(self):
    """Starts the profiling."""
    self._profiling_sample = 0

    if self._memory_profiler:
      self._memory_profiler.Start()

  def _ProfilingStop(self):
    """Stops the profiling."""
    if self._memory_profiler:
      self._memory_profiler.Sample()

    if self._parsers_profiler:
      self._parsers_profiler.Write()

  @property
  def current_path_spec(self):
    """The current path specification."""
    if not self._current_file_entry:
      return
    return self._current_file_entry.path_spec

  def GetStatus(self):
    """Returns a dictionary containing the status."""
    return {
        u'consumed_number_of_path_specs': self.number_of_consumed_items,
        u'display_name': self._current_display_name,
        u'identifier': self._identifier_string,
        u'number_of_events': self._parser_mediator.number_of_events,
        u'processing_status': self._status,
        u'produced_number_of_path_specs': self._produced_number_of_path_specs,
        u'type': definitions.PROCESS_TYPE_WORKER}

  def InitializeParserObjects(self, parser_filter_string=None):
    """Initializes the parser objects.

    The parser_filter_string is a simple comma separated value string that
    denotes a list of parser names to include and/or exclude. Each entry
    can have the value of:

    * Exact match of a list of parsers, or a preset (see
      plaso/frontend/presets.py for a full list of available presets).
    * A name of a single parser (case insensitive), eg. msiecfparser.
    * A glob name for a single parser, eg: '*msie*' (case insensitive).

    Args:
      parser_filter_string: Optional parser filter string.
    """
    self._specification_store, non_sigscan_parser_names = (
        parsers_manager.ParsersManager.GetSpecificationStore(
            parser_filter_string=parser_filter_string))

    self._non_sigscan_parser_names = []
    for parser_name in non_sigscan_parser_names:
      if parser_name in [u'filestat', u'usnjrnl']:
        continue
      self._non_sigscan_parser_names.append(parser_name)

    self._file_scanner = parsers_manager.ParsersManager.GetScanner(
        self._specification_store)

    self._parser_objects = parsers_manager.ParsersManager.GetParserObjects(
        parser_filter_string=parser_filter_string)

    self._filestat_parser_object = self._parser_objects.get(u'filestat', None)
    if u'filestat' in self._parser_objects:
      del self._parser_objects[u'filestat']

    self._usnjrnl_parser_object = self._parser_objects.get(u'usnjrnl', None)
    if u'usnjrnl' in self._parser_objects:
      del self._parser_objects[u'usnjrnl']

  def Run(self):
    """Extracts event objects from file entries."""
    self._parser_mediator.ResetCounters()

    if self._enable_profiling:
      self._ProfilingStart()

    self._status = definitions.PROCESSING_STATUS_RUNNING

    logging.debug(
        u'Worker {0:d} (PID: {1:d}) started monitoring process queue.'.format(
            self._identifier, os.getpid()))

    self.ConsumeItems()

    logging.debug(
        u'Worker {0:d} (PID: {1:d}) stopped monitoring process queue.'.format(
            self._identifier, os.getpid()))

    self._status = definitions.PROCESSING_STATUS_COMPLETED
    self._current_file_entry = None

    if self._enable_profiling:
      self._ProfilingStop()

  def SetEnableDebugMode(self, enable_debug_mode):
    """Enables or disables debug mode.

    Args:
      enable_debug_mode: boolean value to indicate if the debug mode
                         should be enabled.
    """
    self._enable_debug_mode = enable_debug_mode

  def SetEnableProfiling(
      self, enable_profiling, profiling_sample_rate=1000,
      profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if profiling should
                        be enabled.
      profiling_sample_rate: optional integer indicating the profiling sample
                             rate. The value contains the number of files
                             processed. The default value is 1000.
      profiling_type: optional profiling type.
    """
    self._enable_profiling = enable_profiling
    self._profiling_sample_rate = profiling_sample_rate

    if self._enable_profiling:
      if profiling_type in [u'all', u'memory'] and not self._memory_profiler:
        self._memory_profiler = profiler.GuppyMemoryProfiler(self._identifier)

      if profiling_type in [u'all', u'parsers'] and not self._parsers_profiler:
        self._parsers_profiler = profiler.ParsersProfiler(self._identifier)

  def SetFilterObject(self, filter_object):
    """Sets the filter object.

    Args:
      filter_object: the filter object (instance of objectfilter.Filter).
    """
    self._parser_mediator.SetFilterObject(filter_object)

  def SetHashers(self, hasher_names_string):
    """Initializes the hasher objects.

    Args:
      hasher_names_string: Comma separated string of names of
                           hashers to enable.
    """
    names = hashers_manager.HashersManager.GetHasherNamesFromString(
        hasher_names_string)
    logging.debug(u'[SetHashers] Enabling hashers: {0:s}.'.format(names))
    self._hasher_names = names

  def SetMountPath(self, mount_path):
    """Sets the mount path.

    Args:
      mount_path: string containing the mount path.
    """
    self._parser_mediator.SetMountPath(mount_path)

  def SetProcessArchiveFiles(self, process_archive_files):
    """Sets the process archive files mode.

    Args:
      process_archive_files: boolean value to indicate if the worker should
                             scan for file entries inside files.
    """
    self._process_archive_files = process_archive_files

  def SetTextPrepend(self, text_prepend):
    """Sets the text prepend.

    Args:
      text_prepend: string that contains the text to prepend to every
                    event object.
    """
    self._parser_mediator.SetTextPrepend(text_prepend)

  def SignalAbort(self):
    """Signals the worker to abort."""
    self._parser_mediator.SignalAbort()
    super(BaseEventExtractionWorker, self).SignalAbort()
