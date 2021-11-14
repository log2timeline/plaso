# -*- coding: utf-8 -*-
"""The event extraction worker."""

import copy
import os
import re
import time

from dfvfs.analyzer import analyzer as dfvfs_analyzer
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.analyzers import hashing_analyzer
from plaso.analyzers import manager as analyzers_manager
from plaso.containers import event_sources
from plaso.containers import events
from plaso.engine import extractors
from plaso.engine import logger
from plaso.lib import definitions
from plaso.lib import errors


class EventExtractionWorker(object):
  """Event extraction worker.

  The event extraction worker determines which parsers are suitable for parsing
  a particular file entry or data stream. The parsers extract relevant data from
  file system and or file content data. All extracted data is passed to the
  parser mediator for further processing.

  Attributes:
    last_activity_timestamp (int): timestamp received that indicates the last
        time activity was observed.
    processing_status (str): human readable status indication such as:
        'Extracting', 'Hashing'.
  """

  # NTFS metadata files that need special handling.
  _METADATA_FILE_LOCATIONS_NTFS = frozenset([
      '\\$AttrDef',
      '\\$BadClus',
      '\\$Bitmap',
      '\\$Boot',
      '\\$Extend\\$ObjId',
      '\\$Extend\\$Quota',
      '\\$Extend\\$Reparse',
      '\\$Extend\\$RmMetadata\\$Repair',
      '\\$Extend\\$RmMetadata\\$TxfLog\\$Tops',
      '\\$Extend\\$UsnJrnl',
      '\\$LogFile',
      '\\$MFT',
      '\\$MFTMirr',
      '\\$Secure',
      '\\$UpCase',
      '\\$Volume',
  ])

  # TSK metadata files that need special handling.
  _METADATA_FILE_LOCATIONS_TSK = frozenset([
      # NTFS
      '/$AttrDef',
      '/$BadClus',
      '/$Bitmap',
      '/$Boot',
      '/$Extend/$ObjId',
      '/$Extend/$Quota',
      '/$Extend/$Reparse',
      '/$Extend/$RmMetadata/$Repair',
      '/$Extend/$RmMetadata/$TxfLog/$Tops',
      '/$Extend/$UsnJrnl',
      '/$LogFile',
      '/$MFT',
      '/$MFTMirr',
      '/$Secure',
      '/$UpCase',
      '/$Volume',
      # HFS+/HFSX
      '/$ExtentsFile',
      '/$CatalogFile',
      '/$BadBlockFile',
      '/$AllocationFile',
      '/$AttributesFile',
  ])

  # TODO: make this filtering solution more generic. Also see:
  # https://github.com/log2timeline/plaso/issues/467
  _CHROME_CACHE_DATA_FILE_RE = re.compile(r'^[fF]_[0-9a-fA-F]{6}$')
  _FIREFOX_CACHE_DATA_FILE_RE = re.compile(r'^[0-9a-fA-F]{5}[dm][0-9]{2}$')
  _FIREFOX_CACHE2_DATA_FILE_RE = re.compile(r'^[0-9a-fA-F]{40}$')

  _TYPES_WITH_ROOT_METADATA = frozenset([
      dfvfs_definitions.TYPE_INDICATOR_GZIP])

  def __init__(self, force_parser=False, parser_filter_expression=None):
    """Initializes an event extraction worker.

    Args:
      force_parser (Optional[bool]): True if a specified parser should be forced
          to be used to extract events.
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

          A parser filter expression is a comma separated value string that
          denotes which parsers and plugins should be used. See
          filters/parser_filter.py for details of the expression syntax.

          This function does not support presets, and requires a parser
          filter expression where presets have been expanded.
    """
    super(EventExtractionWorker, self).__init__()
    self._abort = False
    self._analyzers = []
    self._analyzers_profiler = None
    self._event_extractor = extractors.EventExtractor(
        force_parser=force_parser,
        parser_filter_expression=parser_filter_expression)
    self._force_parser = force_parser
    self._hasher_file_size_limit = None
    self._path_spec_extractor = extractors.PathSpecExtractor()
    self._process_archives = None
    self._process_compressed_streams = None
    self._processing_profiler = None

    self.last_activity_timestamp = 0.0
    self.processing_status = definitions.STATUS_INDICATOR_IDLE

  def _AnalyzeDataStream(
      self, file_entry, data_stream_name, display_name, event_data_stream):
    """Analyzes the contents of a specific data stream of a file entry.

    The results of the analyzers are set in the event data stream as
    attributes that are added to produced event objects. Note that some
    file systems allow directories to have data streams, such as NTFS.

    Args:
      file_entry (dfvfs.FileEntry): file entry whose data stream is to be
          analyzed.
      data_stream_name (str): name of the data stream.
      display_name (str): human readable representation of the file entry
          currently being analyzed.
      event_data_stream (EventDataStream): event data stream attribute
           container.

    Raises:
      RuntimeError: if the file-like object cannot be retrieved from
          the file entry.
    """
    logger.debug('[AnalyzeDataStream] analyzing file: {0:s}'.format(
        display_name))

    if self._processing_profiler:
      self._processing_profiler.StartTiming('analyzing')

    try:
      file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)
      if not file_object:
        raise RuntimeError((
            'Unable to retrieve file-like object for file entry: '
            '{0:s}.').format(display_name))

      self._AnalyzeFileObject(file_object, display_name, event_data_stream)

    finally:
      if self._processing_profiler:
        self._processing_profiler.StopTiming('analyzing')

    logger.debug('[AnalyzeDataStream] completed analyzing file: {0:s}'.format(
        display_name))

  def _AnalyzeFileObject(self, file_object, display_name, event_data_stream):
    """Processes a file-like object with analyzers.

    Args:
      file_object (dfvfs.FileIO): file-like object to process.
      display_name (str): human readable representation of the file entry
          currently being analyzed.
      event_data_stream (EventDataStream): event data stream attribute
           container.
    """
    maximum_read_size = max([
        analyzer_object.SIZE_LIMIT for analyzer_object in self._analyzers])

    hashers_only = True
    for analyzer_object in self._analyzers:
      if not isinstance(analyzer_object, hashing_analyzer.HashingAnalyzer):
        hashers_only = False
        break

    file_size = file_object.get_size()

    if (hashers_only and self._hasher_file_size_limit and
        file_size > self._hasher_file_size_limit):
      return

    file_object.seek(0, os.SEEK_SET)

    data = file_object.read(maximum_read_size)
    while data:
      if self._abort:
        break

      for analyzer_object in self._analyzers:
        if self._abort:
          break

        if (not analyzer_object.INCREMENTAL_ANALYZER and
            file_size > analyzer_object.SIZE_LIMIT):
          continue

        if (isinstance(analyzer_object, hashing_analyzer.HashingAnalyzer) and
            self._hasher_file_size_limit and
            file_size > self._hasher_file_size_limit):
          continue

        self.processing_status = analyzer_object.PROCESSING_STATUS_HINT

        if self._analyzers_profiler:
          self._analyzers_profiler.StartTiming(analyzer_object.NAME)

        try:
          analyzer_object.Analyze(data)
        finally:
          if self._analyzers_profiler:
            self._analyzers_profiler.StopTiming(analyzer_object.NAME)

        self.last_activity_timestamp = time.time()

      data = file_object.read(maximum_read_size)

    for analyzer_object in self._analyzers:
      for result in analyzer_object.GetResults():
        logger.debug((
            '[AnalyzeFileObject] attribute {0:s}:{1:s} calculated for '
            'file: {2:s}.').format(
                result.attribute_name, result.attribute_value, display_name))

        setattr(event_data_stream, result.attribute_name,
                result.attribute_value)

      analyzer_object.Reset()

    self.processing_status = definitions.STATUS_INDICATOR_RUNNING

  def _CanSkipDataStream(self, file_entry, data_stream):
    """Determines if analysis and extraction of a data stream can be skipped.

    This is used to prevent Plaso trying to run analyzers or extract content
    from a pipe or socket it encounters while processing a mounted filesystem.

    Args:
      file_entry (dfvfs.FileEntry): file entry to consider for skipping.
      data_stream (dfvfs.DataStream): data stream to consider for skipping.

    Returns:
      bool: True if the data stream can be skipped.
    """
    if file_entry.IsFile():
      return False

    if data_stream.IsDefault():
      return True

    return False

  def _CanSkipContentExtraction(self, file_entry):
    """Determines if content extraction of a file entry can be skipped.

    Args:
      file_entry (dfvfs.FileEntry): file entry of which to determine content
          extraction can be skipped.

    Returns:
      bool: True if content extraction can be skipped.
    """
    if self._force_parser:
      return False

    # TODO: make this filtering solution more generic. Also see:
    # https://github.com/log2timeline/plaso/issues/467
    location = getattr(file_entry.path_spec, 'location', None)
    if not location:
      return False

    data_stream_name = getattr(file_entry.path_spec, 'data_stream', None)
    if data_stream_name:
      return False

    file_system = file_entry.GetFileSystem()

    path_segments = file_system.SplitPath(location)
    if not path_segments:
      return False

    if self._CHROME_CACHE_DATA_FILE_RE.match(path_segments[-1]):
      location_segments = path_segments[:-1]
      location_segments.append('index')
      location = file_system.JoinPath(location_segments)
      index_path_spec = path_spec_factory.Factory.NewPathSpec(
          file_entry.type_indicator, location=location,
          parent=file_entry.path_spec.parent)

      if file_system.FileEntryExistsByPathSpec(index_path_spec):
        # TODO: improve this check if "index" is a Chrome Cache index file.
        return True

    elif self._FIREFOX_CACHE_DATA_FILE_RE.match(path_segments[-1]):
      location_segments = path_segments[:-4]
      location_segments.append('_CACHE_MAP_')
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
      location_segments.append('index')
      location = file_system.JoinPath(location_segments)
      index_path_spec = path_spec_factory.Factory.NewPathSpec(
          file_entry.type_indicator, location=location,
          parent=file_entry.path_spec.parent)

      if file_system.FileEntryExistsByPathSpec(index_path_spec):
        # TODO: improve this check if "index" is a Firefox Cache version 2
        # index file.
        return True

    elif len(path_segments) == 1 and path_segments[0].lower() in (
        'hiberfil.sys', 'pagefile.sys', 'swapfile.sys'):
      return True

    elif (len(path_segments) == 4 and
          path_segments[0].lower() == 'private' and
          path_segments[1].lower() == 'var' and
          path_segments[2].lower() == 'vm' and
          path_segments[3].lower() in (
              'sleepimage', 'swapfile0', 'swapfile1')):
      return True

    return False

  def _ExtractContentFromDataStream(
      self, mediator, file_entry, data_stream_name):
    """Extracts content from a data stream.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      file_entry (dfvfs.FileEntry): file entry to extract its content.
      data_stream_name (str): name of the data stream whose content is to be
          extracted.
    """
    self.processing_status = definitions.STATUS_INDICATOR_EXTRACTING

    if self._processing_profiler:
      self._processing_profiler.StartTiming('extracting')

    self._event_extractor.ParseDataStream(
        mediator, file_entry, data_stream_name)

    if self._processing_profiler:
      self._processing_profiler.StopTiming('extracting')

    self.processing_status = definitions.STATUS_INDICATOR_RUNNING

    self.last_activity_timestamp = time.time()

  def _ExtractMetadataFromFileEntry(self, mediator, file_entry, data_stream):
    """Extracts metadata from a file entry.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      file_entry (dfvfs.FileEntry): file entry to extract metadata from.
      data_stream (dfvfs.DataStream): data stream or None if the file entry
          has no data stream.
    """
    # Do not extract metadata from the root file entry when it is virtual.
    if file_entry.IsRoot() and file_entry.type_indicator not in (
        self._TYPES_WITH_ROOT_METADATA):
      return

    # We always want to extract the file entry metadata but we only want
    # to parse it once per file entry, so we only use it if we are
    # processing the default data stream of regular files.
    if data_stream and not data_stream.IsDefault():
      return

    display_name = mediator.GetDisplayName()
    logger.debug(
        '[ExtractMetadataFromFileEntry] processing file entry: {0:s}'.format(
            display_name))

    self.processing_status = definitions.STATUS_INDICATOR_EXTRACTING

    if self._processing_profiler:
      self._processing_profiler.StartTiming('extracting')

    self._event_extractor.ParseFileEntryMetadata(mediator, file_entry)

    if self._processing_profiler:
      self._processing_profiler.StopTiming('extracting')

    self.processing_status = definitions.STATUS_INDICATOR_RUNNING

  def _GetArchiveTypes(self, mediator, path_spec):
    """Determines if a data stream contains an archive such as: TAR or ZIP.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      path_spec (dfvfs.PathSpec): path specification of the data stream.

    Returns:
      list[str]: dfVFS archive type indicators found in the data stream.
    """
    try:
      type_indicators = dfvfs_analyzer.Analyzer.GetArchiveTypeIndicators(
          path_spec, resolver_context=mediator.resolver_context)
    except IOError as exception:
      type_indicators = []

      warning_message = (
          'analyzer failed to determine archive type indicators '
          'with error: {0!s}').format(exception)
      mediator.ProduceExtractionWarning(warning_message, path_spec=path_spec)

    return type_indicators

  def _GetCompressedStreamTypes(self, mediator, path_spec):
    """Determines if a data stream contains a compressed stream such as: gzip.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      path_spec (dfvfs.PathSpec): path specification of the data stream.

    Returns:
      list[str]: dfVFS compressed stream type indicators found in
          the data stream.
    """
    try:
      type_indicators = (
          dfvfs_analyzer.Analyzer.GetCompressedStreamTypeIndicators(
              path_spec, resolver_context=mediator.resolver_context))
    except IOError as exception:
      type_indicators = []

      warning_message = (
          'analyzer failed to determine compressed stream type indicators '
          'with error: {0!s}').format(exception)
      mediator.ProduceExtractionWarning(warning_message, path_spec=path_spec)

    return type_indicators

  def _IsMetadataFile(self, file_entry):
    """Determines if the file entry is a metadata file.

    Args:
      file_entry (dfvfs.FileEntry): a file entry object.

    Returns:
      bool: True if the file entry is a metadata file.
    """
    if (file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_NTFS and
        file_entry.path_spec.location in self._METADATA_FILE_LOCATIONS_NTFS):
      return True

    if (file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK and
        file_entry.path_spec.location in self._METADATA_FILE_LOCATIONS_TSK):
      return True

    return False

  def _ProcessArchiveTypes(self, mediator, path_spec, type_indicators):
    """Processes a data stream containing archive types such as: TAR or ZIP.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      path_spec (dfvfs.PathSpec): path specification.
      type_indicators(list[str]): dfVFS archive type indicators found in
          the data stream.
    """
    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return

    self.processing_status = definitions.STATUS_INDICATOR_COLLECTING

    if number_of_type_indicators > 1:
      display_name = mediator.GetDisplayName()
      logger.debug((
          'Found multiple format type indicators: {0:s} for '
          'archive file: {1:s}').format(type_indicators, display_name))

    for type_indicator in type_indicators:
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_TAR:
        archive_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TAR, location='/',
            parent=path_spec)

      elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_ZIP:
        archive_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_ZIP, location='/',
            parent=path_spec)

      else:
        archive_path_spec = None

        warning_message = (
            'unsupported archive format type indicator: {0:s}').format(
                type_indicator)
        mediator.ProduceExtractionWarning(
            warning_message, path_spec=path_spec)

      if archive_path_spec:
        try:
          path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
              [archive_path_spec], resolver_context=mediator.resolver_context)

          for generated_path_spec in path_spec_generator:
            if self._abort:
              break

            event_source = event_sources.FileEntryEventSource(
                file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_FILE,
                path_spec=generated_path_spec)
            mediator.ProduceEventSource(event_source)

            self.last_activity_timestamp = time.time()

        except (IOError, errors.MaximumRecursionDepth) as exception:
          warning_message = (
              'unable to process archive file with error: {0!s}').format(
                  exception)
          mediator.ProduceExtractionWarning(
              warning_message, path_spec=generated_path_spec)

  def _ProcessCompressedStreamTypes(self, mediator, path_spec, type_indicators):
    """Processes a data stream containing compressed stream types such as: bz2.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      path_spec (dfvfs.PathSpec): path specification.
      type_indicators(list[str]): dfVFS archive type indicators found in
          the data stream.
    """
    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return

    self.processing_status = definitions.STATUS_INDICATOR_COLLECTING

    if number_of_type_indicators > 1:
      display_name = mediator.GetDisplayName()
      logger.debug((
          'Found multiple format type indicators: {0:s} for '
          'compressed stream file: {1:s}').format(
              type_indicators, display_name))

    for type_indicator in type_indicators:
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_BZIP2:
        compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=dfvfs_definitions.COMPRESSION_METHOD_BZIP2,
            parent=path_spec)

      elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_GZIP:
        compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=path_spec)

      elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_XZ:
        compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=dfvfs_definitions.COMPRESSION_METHOD_XZ,
            parent=path_spec)

      else:
        compressed_stream_path_spec = None

        warning_message = (
            'unsupported compressed stream format type indicators: '
            '{0:s}').format(type_indicator)
        mediator.ProduceExtractionWarning(
            warning_message, path_spec=path_spec)

      if compressed_stream_path_spec:
        event_source = event_sources.FileEntryEventSource(
            file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_FILE,
            path_spec=compressed_stream_path_spec)
        mediator.ProduceEventSource(event_source)

        self.last_activity_timestamp = time.time()

  def _ProcessDirectory(self, mediator, file_entry):
    """Processes a directory file entry.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      file_entry (dfvfs.FileEntry): file entry of the directory.
    """
    self.processing_status = definitions.STATUS_INDICATOR_COLLECTING

    if self._processing_profiler:
      self._processing_profiler.StartTiming('collecting')

    for sub_file_entry in file_entry.sub_file_entries:
      if self._abort:
        break

      try:
        if not sub_file_entry.IsAllocated():
          continue

      except dfvfs_errors.BackEndError as exception:
        warning_message = (
            'unable to process directory entry: {0:s} with error: '
            '{1!s}').format(sub_file_entry.name, exception)
        mediator.ProduceExtractionWarning(
            warning_message, path_spec=file_entry.path_spec)
        continue

      # For TSK-based file entries only, ignore the virtual /$OrphanFiles
      # directory.
      if sub_file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
        if file_entry.IsRoot() and sub_file_entry.name == '$OrphanFiles':
          continue

      event_source = event_sources.FileEntryEventSource(
          file_entry_type=sub_file_entry.entry_type,
          path_spec=sub_file_entry.path_spec)

      mediator.ProduceEventSource(event_source)

      self.last_activity_timestamp = time.time()

    if self._processing_profiler:
      self._processing_profiler.StopTiming('collecting')

    self.processing_status = definitions.STATUS_INDICATOR_RUNNING

  def _ProcessFileEntry(self, mediator, file_entry):
    """Processes a file entry.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      file_entry (dfvfs.FileEntry): file entry.
    """
    display_name = mediator.GetDisplayName()
    logger.debug(
        '[ProcessFileEntry] processing file entry: {0:s}'.format(display_name))

    if self._IsMetadataFile(file_entry):
      self._ProcessMetadataFile(mediator, file_entry)

    else:
      file_entry_processed = False
      for data_stream in file_entry.data_streams:
        if self._abort:
          break

        if self._CanSkipDataStream(file_entry, data_stream):
          logger.debug((
              '[ProcessFileEntry] Skipping datastream {0:s} for {1:s}: '
              '{2:s}').format(
                  data_stream.name, file_entry.type_indicator, display_name))
          continue

        self._ProcessFileEntryDataStream(mediator, file_entry, data_stream)

        file_entry_processed = True

      if not file_entry_processed:
        # For when the file entry does not contain a data stream.
        self._ProcessFileEntryDataStream(mediator, file_entry, None)

    logger.debug(
        '[ProcessFileEntry] done processing file entry: {0:s}'.format(
            display_name))

  def _ProcessFileEntryDataStream(self, mediator, file_entry, data_stream):
    """Processes a specific data stream of a file entry.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      file_entry (dfvfs.FileEntry): file entry containing the data stream.
      data_stream (dfvfs.DataStream): data stream or None if the file entry
          has no data stream.
    """
    display_name = mediator.GetDisplayName()
    data_stream_name = getattr(data_stream, 'name', '') or ''
    logger.debug((
        '[ProcessFileEntryDataStream] processing data stream: "{0:s}" of '
        'file entry: {1:s}').format(data_stream_name, display_name))

    event_data_stream = None
    if data_stream:
      display_name = mediator.GetDisplayName()

      path_spec = copy.deepcopy(file_entry.path_spec)
      if not data_stream.IsDefault():
        path_spec.data_stream = data_stream.name

      event_data_stream = events.EventDataStream()
      event_data_stream.path_spec = path_spec

      if self._analyzers:
        # Since AnalyzeDataStream generates event data stream attributes it
        # needs to be called before producing events.
        self._AnalyzeDataStream(
            file_entry, data_stream.name, display_name, event_data_stream)

    mediator.ProduceEventDataStream(event_data_stream)

    self._ExtractMetadataFromFileEntry(mediator, file_entry, data_stream)

    # Not every file entry has a data stream. In such cases we want to
    # extract the metadata only.
    if not data_stream:
      return

    # Determine if the content of the file entry should not be extracted.
    skip_content_extraction = self._CanSkipContentExtraction(file_entry)
    if skip_content_extraction:
      display_name = mediator.GetDisplayName()
      logger.debug(
          'Skipping content extraction of: {0:s}'.format(display_name))
      self.processing_status = definitions.STATUS_INDICATOR_IDLE
      return

    # TODO: merge with previous deepcopy
    path_spec = copy.deepcopy(file_entry.path_spec)
    if data_stream and not data_stream.IsDefault():
      path_spec.data_stream = data_stream.name

    archive_types = []
    compressed_stream_types = []

    if self._process_compressed_streams:
      compressed_stream_types = self._GetCompressedStreamTypes(
          mediator, path_spec)

    if not compressed_stream_types:
      archive_types = self._GetArchiveTypes(mediator, path_spec)

    if archive_types:
      if self._process_archives:
        self._ProcessArchiveTypes(mediator, path_spec, archive_types)

      if dfvfs_definitions.TYPE_INDICATOR_ZIP in archive_types:
        # ZIP files are the base of certain file formats like docx.
        self._ExtractContentFromDataStream(
            mediator, file_entry, data_stream.name)

    elif compressed_stream_types:
      self._ProcessCompressedStreamTypes(
          mediator, path_spec, compressed_stream_types)

    else:
      self._ExtractContentFromDataStream(
          mediator, file_entry, data_stream.name)

  def _ProcessMetadataFile(self, mediator, file_entry):
    """Processes a metadata file.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      file_entry (dfvfs.FileEntry): file entry of the metadata file.
    """
    self.processing_status = definitions.STATUS_INDICATOR_EXTRACTING

    self._event_extractor.ParseFileEntryMetadata(mediator, file_entry)
    for data_stream in file_entry.data_streams:
      if self._abort:
        break

      path_spec = copy.deepcopy(file_entry.path_spec)
      if not data_stream.IsDefault():
        path_spec.data_stream = data_stream.name

      event_data_stream = events.EventDataStream()
      event_data_stream.path_spec = path_spec

      mediator.ProduceEventDataStream(event_data_stream)

      self.last_activity_timestamp = time.time()

      self._event_extractor.ParseMetadataFile(
          mediator, file_entry, data_stream.name)

  def _SetHashers(self, hasher_names_string):
    """Sets the hasher names.

    Args:
      hasher_names_string (str): comma separated names of the hashers
          to enable, where 'none' disables the hashing analyzer.
    """
    if not hasher_names_string or hasher_names_string == 'none':
      return

    analyzer_object = analyzers_manager.AnalyzersManager.GetAnalyzerInstance(
        'hashing')
    analyzer_object.SetHasherNames(hasher_names_string)
    self._analyzers.append(analyzer_object)

  def _SetYaraRules(self, yara_rules_string):
    """Sets the Yara rules.

    Args:
      yara_rules_string (str): unparsed Yara rule definitions.
    """
    if not yara_rules_string:
      return

    analyzer_object = analyzers_manager.AnalyzersManager.GetAnalyzerInstance(
        'yara')
    analyzer_object.SetRules(yara_rules_string)
    self._analyzers.append(analyzer_object)

  def GetAnalyzerNames(self):
    """Gets the names of the active analyzers.

    Returns:
      list[str]: names of active analyzers.
    """
    return [analyzer_instance.NAME for analyzer_instance in self._analyzers]

  def ProcessPathSpec(self, mediator, path_spec, excluded_find_specs=None):
    """Processes a path specification.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      path_spec (dfvfs.PathSpec): path specification.
      excluded_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
         that are excluded from processing.
    """
    self.last_activity_timestamp = time.time()
    self.processing_status = definitions.STATUS_INDICATOR_RUNNING

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        path_spec, resolver_context=mediator.resolver_context)

    if file_entry is None:
      display_name = mediator.GetDisplayNameForPathSpec(path_spec)
      logger.warning(
          'Unable to open file entry with path spec: {0:s}'.format(
              display_name))
      self.processing_status = definitions.STATUS_INDICATOR_IDLE
      return

    for find_spec in excluded_find_specs or []:
      if find_spec.CompareLocation(file_entry):
        logger.info('Skipped: {0:s} because of exclusion filter.'.format(
            file_entry.path_spec.location))
        self.processing_status = definitions.STATUS_INDICATOR_IDLE
        return

    mediator.SetFileEntry(file_entry)

    try:
      if file_entry.IsDirectory():
        self._ProcessDirectory(mediator, file_entry)
      self._ProcessFileEntry(mediator, file_entry)

    finally:
      mediator.ResetFileEntry()

      self.last_activity_timestamp = time.time()
      self.processing_status = definitions.STATUS_INDICATOR_IDLE

  # TODO: move the functionality of this method into the constructor.
  def SetExtractionConfiguration(self, configuration):
    """Sets the extraction configuration settings.

    Args:
      configuration (ExtractionConfiguration): extraction configuration.
    """
    self._hasher_file_size_limit = configuration.hasher_file_size_limit
    self._SetHashers(configuration.hasher_names_string)
    self._process_archives = configuration.process_archives
    self._process_compressed_streams = configuration.process_compressed_streams
    self._SetYaraRules(configuration.yara_rules_string)

  def SetAnalyzersProfiler(self, analyzers_profiler):
    """Sets the analyzers profiler.

    Args:
      analyzers_profiler (AnalyzersProfiler): analyzers profile.
    """
    self._analyzers_profiler = analyzers_profiler

  def SetProcessingProfiler(self, processing_profiler):
    """Sets the processing profiler.

    Args:
      processing_profiler (ProcessingProfiler): processing profile.
    """
    self._processing_profiler = processing_profiler

  def SignalAbort(self):
    """Signals the extraction worker to abort."""
    self._abort = True
