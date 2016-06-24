# -*- coding: utf-8 -*-
"""The event extraction worker."""

import logging
import re

from dfvfs.analyzer import analyzer
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import event_sources
from plaso.engine import extractors
from plaso.engine import profiler
from plaso.hashers import manager as hashers_manager


class EventExtractionWorker(object):
  """Class that defines the event extraction worker base.

  This class is designed to watch a queue for path specifications of files
  and directories (file entries) and data streams for which events need to
  be extracted.

  The event extraction worker needs to determine if a parser suitable
  for parsing a particular file entry or data stream is available. All
  extracted event objects are pushed on a storage queue for further processing.

  Attributes:
    number_of_produced_path_specs: an integer containing the number of
                                   produced path specifications.
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
      self, resolver_context, parser_mediator, parser_filter_expression=None,
      process_archive_files=False):
    """Initializes the event extraction worker object.

    Args:
      resolver_context (dfvfs.Context): resolver context.
      parser_mediator (ParserMediator): parser mediator.
      parser_filter_expression (Optional[str]): parser filter expression.
          None represents all parsers and plugins.

          The parser filter expression is a comma separated value string that
          denotes a list of parser names to include and/or exclude. Each entry
          can have the value of:

          * An exact match of a list of parsers, or a preset (see
            plaso/frontend/presets.py for a full list of available presets).
          * A name of a single parser (case insensitive), e.g. msiecf.
          * A glob name for a single parser, e.g. '*msie*' (case insensitive).

      process_archive_files (Optional[bool]):
          True if the worker should scan for file entries inside archive files.
    """
    super(EventExtractionWorker, self).__init__()
    self._abort = False
    self._current_display_name = u''
    self._current_file_entry = None
    self._enable_debug_mode = False
    self._enable_memory_profiling = False
    self._enable_parsers_profiling = False
    self._event_extractor = extractors.EventExtractor(
        resolver_context, parser_filter_expression=parser_filter_expression)
    self._hasher_names = None
    self._memory_profiler = None
    self._open_files = False
    self._parser_mediator = parser_mediator
    self._process_archive_files = process_archive_files
    self._profiling_sample = 0
    self._profiling_sample_rate = 1000
    self._resolver_context = resolver_context

    self.number_of_produced_path_specs = 0

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

  def _HashDataStream(self, parser_mediator, file_entry, data_stream_name=u''):
    """Hashes the contents of a specific data stream of a file entry.

    The resulting digest hashes are set in the parser mediator as attributes
    that are added to produced event objects. Note that some file systems
    allow directories to have data streams, e.g. NTFS.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_entry: the file entry relating to the data to be hashed (instance of
                  dfvfs.FileEntry)
      data_stream_name: optional data stream name. The default is
                        an empty string which represents the default
                        data stream.

    Raises:
      RuntimeError: if the file-like object is missing.
    """
    if not self._hasher_names:
      return

    logging.debug(u'[HashDataStream] hashing file: {0:s}'.format(
        self._current_display_name))

    file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)
    if not file_object:
      raise RuntimeError(
          u'Unable to retrieve file-like object from file entry.')

    # Make sure frame.f_locals does not keep a reference to file_entry.
    file_entry = None

    try:
      digest_hashes = hashers_manager.HashersManager.HashFileObject(
          self._hasher_names, file_object,
          buffer_size=self._DEFAULT_HASH_READ_SIZE)
    finally:
      file_object.close()

    if self._enable_memory_profiling:
      self._ProfilingSampleMemory()

    for hash_name, digest_hash_string in iter(digest_hashes.items()):
      attribute_name = u'{0:s}_hash'.format(hash_name)
      parser_mediator.AddEventAttribute(attribute_name, digest_hash_string)

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

  def _ProcessArchiveFile(self, parser_mediator, file_entry):
    """Processes an archive file (file that contains file entries).

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
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
          # TODO: make sure to handle the abort here.

          # TODO: change this to pass the archive file path spec to
          # the collector process and have the collector implement a maximum
          # path spec "depth" to prevent ZIP bombs and equiv.
          path_spec_extractor = extractors.PathSpecExtractor(
              self._resolver_context)

          for path_spec in path_spec_extractor.ExtractPathSpecs(
              [archive_path_spec]):
            parser_mediator.ProduceEventSource(path_spec)
            self.number_of_produced_path_specs += 1

        except IOError:
          logging.warning(u'Unable to process archive file:\n{0:s}'.format(
              self._current_display_name))

          # Make sure frame.f_locals does not keep a reference to file_entry.
          file_entry = None

    return True

  def _ProcessCompressedStreamFile(self, parser_mediator, file_entry):
    """Processes an compressed stream file (file that contains file entries).

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
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
        event_source = event_sources.EventSource(
            path_spec=compressed_stream_path_spec)
        parser_mediator.ProduceEventSource(event_source)
        self.number_of_produced_path_specs += 1

    return True

  def _ProcessFileEntry(
      self, parser_mediator, file_entry, data_stream_name=u''):
    """Processes a specific data stream of a file entry.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      data_stream_name: optional data stream name. The default is
                        an empty string which represents the default
                        data stream.

    Raises:
      RuntimeError: if the parser object is missing.
    """
    self._current_file_entry = file_entry
    self._current_display_name = parser_mediator.GetDisplayName(file_entry)

    reference_count = self._resolver_context.GetFileObjectReferenceCount(
        file_entry.path_spec)

    parser_mediator.SetFileEntry(file_entry)

    logging.debug(u'[ProcessFileEntry] processing file entry: {0:s}'.format(
        self._current_display_name))

    try:
      if self._IsMetadataFile(file_entry):
        self._event_extractor.ParseFileEntryMetadata(
            parser_mediator, file_entry)

        self._event_extractor.ParseMetadataFile(
            parser_mediator, file_entry, data_stream_name=data_stream_name)

      else:
        # Not every file entry has a data stream. In such cases we want to
        # extract the metadata only.
        has_data_stream = file_entry.HasDataStream(data_stream_name)

        if has_data_stream:
          self._HashDataStream(
              parser_mediator, file_entry, data_stream_name=data_stream_name)

        # We always want to extract the file entry metadata but we only want
        # to parse it once per file entry, so we only use it if we are
        # processing the default (nameless) data stream.
        if not data_stream_name:
          self._event_extractor.ParseFileEntryMetadata(
              parser_mediator, file_entry)

        # Determine if the content of the file entry should not be extracted.
        skip_content_extraction = self._CanSkipContentExtraction(file_entry)
        if skip_content_extraction:
          logging.info(u'Skipping content extraction of: {0:s}'.format(
              self._current_display_name))
        else:
          is_archive = False
          is_compressed_stream = False

          if file_entry.IsFile():
            is_compressed_stream = self._ProcessCompressedStreamFile(
                parser_mediator, file_entry)
            if not is_compressed_stream:
              is_archive = self._ProcessArchiveFile(parser_mediator, file_entry)

          if has_data_stream and not is_archive and not is_compressed_stream:
            self._event_extractor.ParseDataStream(
                parser_mediator, file_entry, data_stream_name=data_stream_name)

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

      parser_mediator.ResetFileEntry()

      # Make sure frame.f_locals does not keep a reference to file_entry.
      file_entry = None

    if self._enable_memory_profiling:
      self._ProfilingSampleMemory()

    logging.debug(
        u'[ProcessFileEntry] done processing file entry: {0:s}'.format(
            self._current_display_name))

  def _ProfilingSampleMemory(self):
    """Create a memory profiling sample."""
    if not self._memory_profiler:
      return

    self._profiling_sample += 1

    if self._profiling_sample >= self._profiling_sample_rate:
      self._memory_profiler.Sample()
      self._profiling_sample = 0

  @property
  def current_display_name(self):
    """The current display name."""
    return self._current_display_name

  @property
  def current_path_spec(self):
    """The current path specification."""
    if not self._current_file_entry:
      return
    return self._current_file_entry.path_spec

  @property
  def number_of_produced_events(self):
    """The number of produced events."""
    # TODO: refactor status indication.
    return self._parser_mediator.number_of_produced_events

  def DisableProfiling(self, profiling_type=u'all'):
    """Disables profiling.

    Args:
      profiling_type: optional profiling type.
    """
    if profiling_type in (u'all', u'memory'):
      self._enable_memory_profiling = False

    if profiling_type in (u'all', u'parsers'):
      self._enable_parsers_profiling = False

  def EnableProfiling(self, profiling_sample_rate=1000, profiling_type=u'all'):
    """Enables profiling.

    Args:
      profiling_sample_rate (Optional[int]): the profiling sample rate.
          Contains the number of event sources processed.
      profiling_type (Optional[str]): type of profiling.
          Supported types are:

          * 'memory' to profile memory usage;
          * 'parsers' to profile CPU time consumed by individual parsers.
    """
    self._profiling_sample_rate = profiling_sample_rate

    if profiling_type in (u'all', u'memory'):
      self._enable_memory_profiling = True

    if profiling_type in (u'all', u'parsers'):
      self._enable_parsers_profiling = True

  def ProcessPathSpec(self, path_spec):
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

      self._ProcessFileEntry(
          self._parser_mediator, file_entry, data_stream_name=data_stream_name)

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
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      logging.warning(
          u'Unhandled exception while processing path spec: {0:s}.'.format(
              path_spec.comparable))
      logging.exception(exception)

      if self._enable_debug_mode:
        self._DebugProcessPathSpec()

    # Make sure frame.f_locals does not keep a reference to file_entry.
    file_entry = None

  def ProfilingStart(self, identifier):
    """Starts profiling.

    Args:
      identifier (str): profiling identifier.

    Raises:
      ValueError: if the memory profiler is already set.
    """
    self._profiling_sample = 0

    if self._enable_memory_profiling:
      if self._memory_profiler:
        raise ValueError(u'Memory profiler already set.')

      self._memory_profiler = profiler.GuppyMemoryProfiler(identifier)
      self._memory_profiler.Start()

    if self._enable_parsers_profiling:
      self._event_extractor.ProfilingStart(identifier)

  def ProfilingStop(self):
    """Stops profiling.

    Raises:
      ValueError: if the memory profiler is not set.
    """
    if self._enable_memory_profiling:
      if not self._memory_profiler:
        raise ValueError(u'Memory profiler not set.')

      self._memory_profiler.Sample()

    if self._enable_parsers_profiling:
      self._event_extractor.ProfilingStop()

  def SetEnableDebugMode(self, enable_debug_mode):
    """Enables or disables debug mode.

    Args:
      enable_debug_mode: boolean value to indicate if the debug mode
                         should be enabled.
    """
    self._enable_debug_mode = enable_debug_mode

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

  def SetTextPrepend(self, text_prepend):
    """Sets the text prepend.

    Args:
      text_prepend: string that contains the text to prepend to every
                    event object.
    """
    self._parser_mediator.SetTextPrepend(text_prepend)

  def SignalAbort(self):
    """Signals the worker to abort."""
    self._abort = True
    self._parser_mediator.SignalAbort()
