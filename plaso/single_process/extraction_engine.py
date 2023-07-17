# -*- coding: utf-8 -*-
"""The single process extraction engine."""

import collections
import os
import pdb
import threading
import time

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import counts
from plaso.containers import event_sources
from plaso.containers import events
from plaso.engine import engine
from plaso.engine import extractors
from plaso.engine import logger
from plaso.engine import process_info
from plaso.engine import timeliner
from plaso.engine import worker
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator


class SingleProcessEngine(engine.BaseEngine):
  """Single process extraction engine."""

  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE

  # Maximum number of dfVFS file system objects to cache.
  _FILE_SYSTEM_CACHE_SIZE = 3

  def __init__(self, status_update_callback=None):
    """Initializes a single process extraction engine.

    Args:
      status_update_callback (Optional[function]): callback function for status
          updates.
    """
    super(SingleProcessEngine, self).__init__()
    self._current_display_name = ''
    self._event_data_timeliner = None
    self._extraction_worker = None
    self._file_system_cache = []
    self._number_of_consumed_event_data = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_events = 0
    self._parser_mediator = None
    self._parsers_counter = None
    self._path_spec_extractor = extractors.PathSpecExtractor()
    self._pid = os.getpid()
    self._process_information = process_info.ProcessInfo(self._pid)
    self._processing_configuration = None
    self._resolver_context = None
    self._status = definitions.STATUS_INDICATOR_IDLE
    self._status_update_active = False
    self._status_update_callback = status_update_callback
    self._status_update_thread = None
    self._storage_writer = None

  def _CacheFileSystem(self, file_system):
    """Caches a dfVFS file system object.

    Keeping and additional reference to a dfVFS file system object causes the
    object to remain cached in the resolver context. This minimizes the number
    times the file system is re-opened.

    Args:
      file_system (dfvfs.FileSystem): file system.
    """
    if file_system not in self._file_system_cache:
      if len(self._file_system_cache) == self._FILE_SYSTEM_CACHE_SIZE:
        self._file_system_cache.pop(0)
      self._file_system_cache.append(file_system)

    elif len(self._file_system_cache) == self._FILE_SYSTEM_CACHE_SIZE:
      # Move the file system to the end of the list to preserve the most
      # recently file system object.
      self._file_system_cache.remove(file_system)
      self._file_system_cache.append(file_system)

  def _CheckExcludedPathSpec(self, file_system, path_spec):
    """Determines if the path specification should be excluded from extraction.

    Args:
      file_system (dfvfs.FileSystem): file system which the path specification
          is part of.
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      bool: True if the path specification should be excluded from extraction.
    """
    for find_spec in self._excluded_file_system_find_specs or []:
      if find_spec.ComparePathSpecLocation(path_spec, file_system):
        return True

    return False

  def _CollectInitialEventSources(
      self, parser_mediator, file_system_path_specs):
    """Collects the initial event sources.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_system_path_specs (list[dfvfs.PathSpec]): path specifications of
          the source file systems to process.
    """
    self._status = definitions.STATUS_INDICATOR_COLLECTING

    included_find_specs = self.GetCollectionIncludedFindSpecs()

    for file_system_path_spec in file_system_path_specs:
      if self._abort:
        break

      file_system = path_spec_resolver.Resolver.OpenFileSystem(
          file_system_path_spec, resolver_context=self._resolver_context)

      path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
          file_system_path_spec, find_specs=included_find_specs,
          recurse_file_system=False, resolver_context=self._resolver_context)
      for path_spec in path_spec_generator:
        if self._abort:
          break

        if self._CheckExcludedPathSpec(file_system, path_spec):
          display_name = parser_mediator.GetDisplayNameForPathSpec(path_spec)
          logger.debug('Excluded from extraction: {0:s}.'.format(display_name))
          continue

        # TODO: determine if event sources should be DataStream or FileEntry
        # or both.
        event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
        parser_mediator.ProduceEventSource(event_source)

  def _ProcessEventData(self):
    """Generate events from event data."""
    if self._processing_profiler:
      self._processing_profiler.StartTiming('process_event_data')

    self._status = definitions.STATUS_INDICATOR_TIMELINING

    if self._processing_profiler:
      self._processing_profiler.StartTiming('get_event_data')

    event_data = self._storage_writer.GetFirstWrittenEventData()

    if self._processing_profiler:
      self._processing_profiler.StopTiming('get_event_data')

    while event_data:
      if self._abort:
        break

      event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()

      event_data_stream = None
      if event_data_stream_identifier:
        if self._processing_profiler:
          self._processing_profiler.StartTiming('get_event_data_stream')

        event_data_stream = (
            self._storage_writer.GetAttributeContainerByIdentifier(
                self._CONTAINER_TYPE_EVENT_DATA_STREAM,
                event_data_stream_identifier))

        if self._processing_profiler:
          self._processing_profiler.StopTiming('get_event_data_stream')

      self._event_data_timeliner.ProcessEventData(
          self._storage_writer, event_data, event_data_stream)

      self._number_of_consumed_event_data += 1
      self._number_of_produced_events += (
          self._event_data_timeliner.number_of_produced_events)

      # TODO: track number of consumed event data containers?

      if self._processing_profiler:
        self._processing_profiler.StartTiming('get_event_data')

      event_data = self._storage_writer.GetNextWrittenEventData()

      if self._processing_profiler:
        self._processing_profiler.StopTiming('get_event_data')

    if self._abort:
      self._status = definitions.STATUS_INDICATOR_ABORTED
    else:
      self._status = definitions.STATUS_INDICATOR_COMPLETED

    if self._processing_profiler:
      self._processing_profiler.StopTiming('process_event_data')

  def _ProcessEventSources(self, storage_writer, parser_mediator):
    """Processes event sources.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    self._status = definitions.STATUS_INDICATOR_RUNNING

    if self._processing_profiler:
      self._processing_profiler.StartTiming('get_event_source')

    event_source = storage_writer.GetFirstWrittenEventSource()

    if self._processing_profiler:
      self._processing_profiler.StopTiming('get_event_source')

    while event_source:
      if self._abort:
        break

      self._ProcessPathSpec(parser_mediator, event_source.path_spec)

      self._number_of_consumed_sources += 1

      if self._processing_profiler:
        self._processing_profiler.StartTiming('get_event_source')

      event_source = storage_writer.GetNextWrittenEventSource()

      if self._processing_profiler:
        self._processing_profiler.StopTiming('get_event_source')

  def _ProcessPathSpec(self, parser_mediator, path_spec):
    """Processes a path specification.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      path_spec (dfvfs.PathSpec): path specification.
    """
    try:
      self._current_display_name = parser_mediator.GetDisplayNameForPathSpec(
          path_spec)

      file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          path_spec, resolver_context=parser_mediator.resolver_context)
      if file_entry is None:
        logger.warning('Unable to open file entry: {0:s}'.format(
            self._current_display_name))
        return

      file_system = file_entry.GetFileSystem()

      if (path_spec and not path_spec.IsSystemLevel() and
          path_spec.type_indicator != dfvfs_definitions.TYPE_INDICATOR_GZIP):
        self._CacheFileSystem(file_system)

      if self._CheckExcludedPathSpec(file_system, path_spec):
        logger.debug('Excluded from extraction: {0:s}.'.format(
            self._current_display_name))
        return

      self._extraction_worker.ProcessFileEntry(parser_mediator, file_entry)

    except KeyboardInterrupt:
      self._abort = True

      self._processing_status.aborted = True
      if self._status_update_callback:
        self._status_update_callback(self._processing_status)

    # All exceptions need to be caught here to prevent the worker
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionWarning((
          'unable to process path specification with error: '
          '{0!s}').format(exception), path_spec=path_spec)

      if getattr(self._processing_configuration, 'debug_output', False):
        self._StopStatusUpdateThread()

        logger.warning(
            'Unhandled exception while processing path spec: {0:s}.'.format(
                self._current_display_name))
        logger.exception(exception)

        pdb.post_mortem()

        self._StartStatusUpdateThread()

  def _ProcessSource(self, parser_mediator, file_system_path_specs):
    """Processes file systems within a source.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_system_path_specs (list[dfvfs.PathSpec]): path specifications of
          the source file systems to process.
    """
    self._current_display_name = ''
    self._number_of_consumed_sources = 0

    if self._processing_profiler:
      self._processing_profiler.StartTiming('process_source')

    self._CollectInitialEventSources(
        parser_mediator, file_system_path_specs)

    self._ProcessEventSources(self._storage_writer, parser_mediator)

    if self._processing_profiler:
      self._processing_profiler.StopTiming('process_source')

    if self._abort:
      self._status = definitions.STATUS_INDICATOR_ABORTED
    else:
      self._status = definitions.STATUS_INDICATOR_COMPLETED

  def _StartStatusUpdateThread(self):
    """Starts the status update thread."""
    self._status_update_active = True
    self._status_update_thread = threading.Thread(
        name='Status update', target=self._StatusUpdateThreadMain)
    self._status_update_thread.start()

  def _StatusUpdateThreadMain(self):
    """Main function of the status update thread."""
    while self._status_update_active:
      self._UpdateStatus()

      time.sleep(self._status_update_interval)

  def _StopStatusUpdateThread(self):
    """Stops the status update thread."""
    if self._status_update_thread:
      self._status_update_active = False
      if self._status_update_thread.is_alive():
        self._status_update_thread.join()
      self._status_update_thread = None

  def _UpdateStatus(self):
    """Updates the processing status."""
    status = self._extraction_worker.processing_status
    if status == definitions.STATUS_INDICATOR_IDLE:
      status = self._status
    if status == definitions.STATUS_INDICATOR_IDLE:
      status = definitions.STATUS_INDICATOR_RUNNING

    used_memory = self._process_information.GetUsedMemory() or 0

    self._processing_status.UpdateForemanStatus(
        self._name, status, self._pid, used_memory, self._current_display_name,
        self._number_of_consumed_sources,
        self._parser_mediator.number_of_produced_event_sources,
        self._number_of_consumed_event_data,
        self._parser_mediator.number_of_produced_event_data,
        0, self._number_of_produced_events,
        0, 0,
        0, 0)

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

  def _CreateParserMediator(
      self, storage_writer, resolver_context, processing_configuration,
      system_configurations):
    """Creates a parser mediator.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      resolver_context (dfvfs.Context): resolver context.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      system_configurations (list[SystemConfigurationArtifact]): system
          configurations.

    Returns:
      ParserMediator: parser mediator.

    Raises:
      BadConfigOption: if an invalid collection filter was specified.
    """
    # TODO: get environment_variables per system_configuration
    environment_variables = None
    if self.knowledge_base:
      environment_variables = self.knowledge_base.GetEnvironmentVariables()

    user_accounts = list(storage_writer.GetAttributeContainers('user_account'))

    try:
      self.BuildCollectionFilters(
          environment_variables, user_accounts,
          artifact_filter_names=processing_configuration.artifact_filters,
          filter_file_path=processing_configuration.filter_file)
    except errors.InvalidFilter as exception:
      raise errors.BadConfigOption(
          'Unable to build collection filters with error: {0!s}'.format(
              exception))

    parser_mediator = parsers_mediator.ParserMediator(
        registry_find_specs=self._registry_find_specs,
        resolver_context=resolver_context,
        system_configurations=system_configurations)

    parser_mediator.SetExtractWinEvtResources(
        processing_configuration.extraction.extract_winevt_resources)
    parser_mediator.SetPreferredCodepage(
        processing_configuration.preferred_codepage)
    parser_mediator.SetPreferredLanguage(
        processing_configuration.preferred_language)
    parser_mediator.SetTemporaryDirectory(
        processing_configuration.temporary_directory)

    return parser_mediator

  def ProcessSource(
      self, storage_writer, resolver_context, processing_configuration,
      system_configurations, file_system_path_specs):
    """Processes file systems within a source.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      resolver_context (dfvfs.Context): resolver context.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      system_configurations (list[SystemConfigurationArtifact]): system
          configurations.
      file_system_path_specs (list[dfvfs.PathSpec]): path specifications of
          the source file systems to process.

    Returns:
      ProcessingStatus: processing status.

    Raises:
      BadConfigOption: if an invalid collection filter was specified or if
          the preferred time zone is invalid.
    """
    if not self._artifacts_registry:
      # TODO: refactor.
      self.BuildArtifactsRegistry(
          processing_configuration.artifact_definitions_path,
          processing_configuration.custom_artifacts_path)

    parser_mediator = self._CreateParserMediator(
        storage_writer, resolver_context, processing_configuration,
        system_configurations)
    parser_mediator.SetStorageWriter(storage_writer)

    self._extraction_worker = worker.EventExtractionWorker(
        force_parser=processing_configuration.force_parser,
        parser_filter_expression=(
            processing_configuration.parser_filter_expression))

    self._extraction_worker.SetExtractionConfiguration(
        processing_configuration.extraction)

    self._event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=processing_configuration.data_location,
        preferred_year=processing_configuration.preferred_year,
        system_configurations=system_configurations)

    try:
      self._event_data_timeliner.SetPreferredTimeZone(
          processing_configuration.preferred_time_zone)
    except ValueError as exception:
      raise errors.BadConfigOption(exception)

    self._parser_mediator = parser_mediator
    self._processing_configuration = processing_configuration
    self._resolver_context = resolver_context
    self._storage_writer = storage_writer

    logger.debug('Processing started.')

    parser_mediator.StartProfiling(
        self._processing_configuration.profiling, self._name,
        self._process_information)
    self._StartProfiling(self._processing_configuration.profiling)

    if self._analyzers_profiler:
      self._extraction_worker.SetAnalyzersProfiler(self._analyzers_profiler)

    if self._processing_profiler:
      self._extraction_worker.SetProcessingProfiler(self._processing_profiler)

    if self._serializers_profiler:
      self._storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._storage_writer.SetStorageProfiler(self._storage_profiler)

    self._StartStatusUpdateThread()

    self._parsers_counter = collections.Counter({
        parser_count.name: parser_count
        for parser_count in self._storage_writer.GetAttributeContainers(
            'parser_count')})

    try:
      self._ProcessSource(parser_mediator, file_system_path_specs)

      self._ProcessEventData()

    finally:
      # Stop the status update thread after close of the storage writer
      # so we include the storage sync to disk in the status updates.
      self._StopStatusUpdateThread()

      if self._analyzers_profiler:
        self._extraction_worker.SetAnalyzersProfiler(None)

      if self._processing_profiler:
        self._extraction_worker.SetProcessingProfiler(None)

      if self._serializers_profiler:
        self._storage_writer.SetSerializersProfiler(None)

      if self._storage_profiler:
        self._storage_writer.SetStorageProfiler(None)

      self._StopProfiling()
      parser_mediator.StopProfiling()

    for key, value in self._event_data_timeliner.parsers_counter.items():
      parser_count = self._parsers_counter.get(key, None)
      if parser_count:
        parser_count.number_of_events += value
        self._storage_writer.UpdateAttributeContainer(parser_count)
      else:
        parser_count = counts.ParserCount(name=key, number_of_events=value)
        self._parsers_counter[key] = parser_count
        self._storage_writer.AddAttributeContainer(parser_count)

    # TODO: remove after completion event and event data split.
    for key, value in parser_mediator.parsers_counter.items():
      parser_count = self._parsers_counter.get(key, None)
      if parser_count:
        parser_count.number_of_events += value
        self._storage_writer.UpdateAttributeContainer(parser_count)
      else:
        parser_count = counts.ParserCount(name=key, number_of_events=value)
        self._parsers_counter[key] = parser_count
        self._storage_writer.AddAttributeContainer(parser_count)

    if self._abort:
      logger.debug('Processing aborted.')
      self._processing_status.aborted = True
    else:
      logger.debug('Processing completed.')

    # Update the status view one last time.
    self._UpdateStatus()

    self._event_data_timeliner = None
    self._extraction_worker = None
    self._file_system_cache = []
    self._parser_mediator = None
    self._processing_configuration = None
    self._resolver_context = None
    self._storage_writer = None

    return self._processing_status
