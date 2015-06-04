# -*- coding: utf-8 -*-
"""The event extraction worker."""

import logging
import os

from dfvfs.analyzer import analyzer
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

import pysigscan

from plaso.engine import collector
from plaso.engine import profiler
from plaso.engine import queue
from plaso.lib import definitions
from plaso.lib import errors
from plaso.hashers import manager as hashers_manager
from plaso.parsers import manager as parsers_manager


class BaseEventExtractionWorker(queue.ItemQueueConsumer):
  """Class that defines the event extraction worker base.

  This class is designed to watch a queue for path specifications of files
  and directories (file entries) for which events need to be extracted.

  The event extraction worker needs to determine if a parser suitable
  for parsing a particular file is available. All extracted event objects
  are pushed on a storage queue for further processing.
  """

  DEFAULT_HASH_READ_SIZE = 4096

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
                        The default is None.
    """
    super(BaseEventExtractionWorker, self).__init__(path_spec_queue)
    self._current_file_entry = False
    self._enable_debug_output = False
    self._identifier = identifier
    self._identifier_string = u'Worker_{0:d}'.format(identifier)
    self._file_scanner = None
    self._filestat_parser_object = None
    self._hasher_names = None
    self._non_sigscan_parser_names = None
    self._number_of_path_specs_produced = 0
    self._open_files = False
    self._parser_mediator = parser_mediator
    self._parser_objects = None
    self._process_archive_files = False
    self._resolver_context = resolver_context
    self._specification_store = None

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

  def _ConsumeItem(self, path_spec, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).
    """
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        path_spec, resolver_context=self._resolver_context)

    if file_entry is None:
      logging.warning(u'Unable to open file entry: {0:s}'.format(
          path_spec.comparable))
      return

    if self._hasher_names:
      try:
        digests = self.HashFileEntry(file_entry)
        if digests:
          for hash_name, digest in digests.iteritems():
            attribute_string = u'{0:s}_hash'.format(hash_name)
            self._parser_mediator.AddEventAttribute(attribute_string, digest)

      except IOError as exception:
        logging.warning(u'Unable to hash file: {0:s} with error: {1:s}'.format(
            path_spec.comparable, exception))

    try:
      self.ParseFileEntry(file_entry)
    except IOError as exception:
      logging.warning(u'Unable to parse file: {0:s} with error: {1:s}'.format(
          path_spec.comparable, exception))

  def _DebugParseFileEntry(self):
    """Callback for debugging file entry parsing failures."""
    return

  def _GetSignatureMatchParserNames(self, file_entry):
    """Determines if a file matches one of the known signatures.

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Returns:
      A list of parser names for which the file entry matches their
      known signatures.
    """
    parser_name_list = []
    scan_state = pysigscan.scan_state()

    file_object = file_entry.GetFileObject()
    try:
      self._file_scanner.scan_file_object(scan_state, file_object)
    finally:
      file_object.close()

    for scan_result in scan_state.scan_results:
      format_specification = (
          self._specification_store.GetSpecificationBySignature(
              scan_result.identifier))

      if format_specification.identifier not in parser_name_list:
        parser_name_list.append(format_specification.identifier)

    return parser_name_list

  def _ParseFileEntryWithParser(self, parser_object, file_entry):
    """Parses a file entry with a specific parser.

    Args:
      parser_object: A parser object (instance of BaseParser).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Raises:
      QueueFull: If a queue is full.
    """
    self._parser_mediator.ClearParserChain()

    reference_count = self._resolver_context.GetFileObjectReferenceCount(
        file_entry.path_spec)

    if self._parsers_profiler:
      self._parsers_profiler.StartTiming(parser_object.NAME)

    try:
      parser_object.UpdateChainAndParse(self._parser_mediator)

    except errors.UnableToParseFile as exception:
      logging.debug(u'Not a {0:s} file ({1:s}) - {2:s}'.format(
          parser_object.NAME, file_entry.name, exception))

    except errors.QueueFull:
      raise

    except IOError as exception:
      logging.debug(
          u'[{0:s}] Unable to parse: {1:s} with error: {2:s}'.format(
              parser_object.NAME, file_entry.path_spec.comparable,
              exception))

    # Casting a wide net, catching all exceptions. Done to keep the worker
    # running, despite the parser hitting errors, so the worker doesn't die
    # if a single file is corrupted or there is a bug in a parser.
    except Exception as exception:
      logging.warning(
          u'[{0:s}] Unable to process file: {1:s} with error: {2:s}.'.format(
              parser_object.NAME, file_entry.path_spec.comparable,
              exception))
      logging.debug(
          u'The path specification that caused the error: {0:s}'.format(
              file_entry.path_spec.comparable))
      logging.exception(exception)
      if self._enable_debug_output:
        self._DebugParseFileEntry()

    finally:
      if self._parsers_profiler:
        self._parsers_profiler.StopTiming(parser_object.NAME)

      if reference_count != self._resolver_context.GetFileObjectReferenceCount(
          file_entry.path_spec):
        logging.warning((
            u'[{0:s}] did not explicitly close file-object for path '
            u'specification: {1:s}.').format(
                parser_object.NAME, file_entry.path_spec.comparable))

  def _ProcessArchiveFile(self, file_entry):
    """Processes an archive file (file that contains file entries).

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file is an archive file.
    """
    type_indicators = analyzer.Analyzer.GetArchiveTypeIndicators(
        file_entry.path_spec, resolver_context=self._resolver_context)

    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return False

    if number_of_type_indicators > 1:
      logging.debug((
          u'Found multiple format type indicators: {0:s} for '
          u'archive file: {1:s}').format(
              type_indicators, file_entry.path_spec.comparable))

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
                type_indicator, file_entry.path_spec.comparable))

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
            self._number_of_path_specs_produced += (
                file_system_collector.number_of_produced_items)

          finally:
            file_system.Close()

        except IOError:
          logging.warning(u'Unable to process archive file:\n{0:s}'.format(
              archive_path_spec.comparable))

    return True

  def _ProcessCompressedStreamFile(self, file_entry):
    """Processes an compressed stream file (file that contains file entries).

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file is a compressed stream file.
    """
    type_indicators = analyzer.Analyzer.GetCompressedStreamTypeIndicators(
        file_entry.path_spec, resolver_context=self._resolver_context)

    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return False

    if number_of_type_indicators > 1:
      logging.debug((
          u'Found multiple format type indicators: {0:s} for '
          u'compressed stream file: {1:s}').format(
              type_indicators, file_entry.path_spec.comparable))

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
                type_indicator, file_entry.path_spec.comparable))

        compressed_stream_path_spec = None

      if compressed_stream_path_spec:
        self._queue.PushItem(compressed_stream_path_spec)
        self._number_of_path_specs_produced += 1

    return True

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
    if self._current_file_entry:
      display_name = self._parser_mediator.GetDisplayName(
          file_entry=self._current_file_entry)
    else:
      display_name = u''

    # TODO: include the path specs generated by the workers.
    number_of_path_specs = (
        self.number_of_consumed_items - self._number_of_path_specs_produced)

    return {
        u'display_name': display_name,
        u'identifier': self._identifier_string,
        u'number_of_events': self._parser_mediator.number_of_events,
        u'number_of_path_specs': number_of_path_specs,
        u'processing_status': self._status,
        u'type': definitions.PROCESS_TYPE_WORKER}

  def HashFileEntry(self, file_entry):
    """Produces a dictionary containing hash digests of the file entry content.

    Args:
      file_entry: The file entry object to be hashed (instance of
                  dfvfs.FileEntry)

    Returns:
      A dictionary mapping hasher names to the digest calculated by that hasher,
      or None if the file_entry is not a file, or no hashers are enabled.
    """
    logging.debug(u'[HashFileEntry] Hashing: {0:s}'.format(
        file_entry.path_spec.comparable))
    if not file_entry.IsFile() or not self._hasher_names:
      return

    hasher_objects = hashers_manager.HashersManager.GetHasherObjects(
        self._hasher_names)

    file_object = file_entry.GetFileObject()
    try:
      file_object.seek(0, os.SEEK_SET)

      # We only do one read, then pass it to each of the hashers in turn.
      data = file_object.read(self.DEFAULT_HASH_READ_SIZE)
      while data:
        for hasher in hasher_objects:
          hasher.Update(data)
        data = file_object.read(self.DEFAULT_HASH_READ_SIZE)

      digests = {}
      # Get the digest values for every active hasher.
      for hasher in hasher_objects:
        digests[hasher.NAME] = hasher.GetStringDigest()
        logging.debug(
            u'[HashFileEntry] Digest {0:s} calculated for {1:s}.'.format(
                hasher.GetStringDigest(), file_entry.path_spec.comparable))
    finally:
      file_object.close()

    if self._enable_profiling:
      self._ProfilingSampleMemory()

    logging.debug(u'[HashFileEntry] Finished hashing: {0:s}'.format(
        file_entry.path_spec.comparable))
    return digests

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
      parser_filter_string: Optional parser filter string. The default is None.
    """
    self._specification_store, self._non_sigscan_parser_names = (
        parsers_manager.ParsersManager.GetSpecificationStore(
            parser_filter_string=parser_filter_string))

    self._file_scanner = parsers_manager.ParsersManager.GetScanner(
        self._specification_store)

    self._parser_objects = parsers_manager.ParsersManager.GetParserObjects(
        parser_filter_string=parser_filter_string)

    self._filestat_parser_object = self._parser_objects.get(u'filestat', None)

  def ParseFileEntry(self, file_entry):
    """Parses a file entry.

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Raises:
      RuntimeError: if the parser object is missing.
    """
    logging.debug(u'[ParseFileEntry] Parsing: {0:s}'.format(
        file_entry.path_spec.comparable))

    self._parser_mediator.SetFileEntry(file_entry)
    self._current_file_entry = file_entry

    reference_count = self._resolver_context.GetFileObjectReferenceCount(
        file_entry.path_spec)

    is_archive = False
    is_compressed_stream = False
    is_file = file_entry.IsFile()

    if is_file:
      is_compressed_stream = self._ProcessCompressedStreamFile(file_entry)
      if not is_compressed_stream:
        is_archive = self._ProcessArchiveFile(file_entry)

    if is_file and not is_archive and not is_compressed_stream:
      parser_name_list = self._GetSignatureMatchParserNames(file_entry)
      if not parser_name_list:
        parser_name_list = self._non_sigscan_parser_names

      for parser_name in parser_name_list:
        parser_object = self._parser_objects.get(parser_name, None)
        if not parser_object:
          self._parser_mediator.ResetFileEntry()
          raise RuntimeError(u'No such parser: {0:s}'.format(parser_name))

        logging.debug(u'Trying to parse: {0:s} with parser: {1:s}'.format(
            file_entry.name, parser_name))

        self._ParseFileEntryWithParser(parser_object, file_entry)

    elif self._filestat_parser_object:
      # TODO: for archive and compressed stream files is the desired behavior
      # to only apply the filestat parser?
      self._ParseFileEntryWithParser(self._filestat_parser_object, file_entry)

    if reference_count != self._resolver_context.GetFileObjectReferenceCount(
        file_entry.path_spec):
      # Clean up after parsers that do not call close explicitly.
      if self._resolver_context.ForceRemoveFileObject(file_entry.path_spec):
        logging.warning((
            u'File-object not explicitly closed for path specification: '
            u'{0:s}.').format(file_entry.path_spec.comparable))

    # We do not clear self._current_file_entry here to allow the foreman
    # to see which file was previously processed.

    logging.debug(u'[ParseFileEntry] Done parsing: {0:s}'.format(
        file_entry.path_spec.comparable))

    self._parser_mediator.ResetFileEntry()

    if self._enable_profiling:
      self._ProfilingSampleMemory()

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

  def SetEnableDebugOutput(self, enable_debug_output):
    """Enables or disables debug output.

    Args:
      enable_debug_output: boolean value to indicate if the debug output
                           should be enabled.
    """
    self._enable_debug_output = enable_debug_output

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
      profiling_type: optional profiling type. The default is 'all'.
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
