# -*- coding: utf-8 -*-
"""The single process processing engine."""

import os
import pdb
import threading
import time

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import resolver

from plaso.containers import event_sources
from plaso.engine import engine
from plaso.engine import extractors
from plaso.engine import logger
from plaso.engine import process_info
from plaso.engine import worker
from plaso.lib import definitions
from plaso.parsers import mediator as parsers_mediator


class SingleProcessEngine(engine.BaseEngine):
  """Class that defines the single process engine."""

  # Maximum number of dfVFS file system objects to cache.
  _FILE_SYSTEM_CACHE_SIZE = 3

  def __init__(self):
    """Initializes a single process engine."""
    super(SingleProcessEngine, self).__init__()
    self._current_display_name = ''
    self._extraction_worker = None
    self._file_system_cache = []
    self._number_of_consumed_sources = 0
    self._path_spec_extractor = extractors.PathSpecExtractor()
    self._pid = os.getpid()
    self._process_information = process_info.ProcessInfo(self._pid)
    self._processing_configuration = None
    self._resolver_context = None
    self._session = None
    self._status = definitions.STATUS_INDICATOR_IDLE
    self._status_update_active = False
    self._status_update_callback = None
    self._status_update_thread = None
    self._storage_writer = None

  def _CacheFileSystem(self, path_spec):
    """Caches a dfVFS file system object.

    Keeping and additional reference to a dfVFS file system object causes the
    object to remain cached in the resolver context. This minimizes the number
    times the file system is re-opened.

    Args:
      path_spec (dfvfs.PathSpec): path specification.
    """
    if (path_spec and not path_spec.IsSystemLevel() and
        path_spec.type_indicator != dfvfs_definitions.TYPE_INDICATOR_GZIP):
      file_system = resolver.Resolver.OpenFileEntry(
          path_spec, resolver_context=self._resolver_context)

      if file_system not in self._file_system_cache:
        if len(self._file_system_cache) == self._FILE_SYSTEM_CACHE_SIZE:
          self._file_system_cache.pop(0)
        self._file_system_cache.append(file_system)

      elif len(self._file_system_cache) == self._FILE_SYSTEM_CACHE_SIZE:
        # Move the file system to the end of the list to preserve the most
        # recently file system object.
        self._file_system_cache.remove(file_system)
        self._file_system_cache.append(file_system)

  def _ProcessPathSpec(self, extraction_worker, parser_mediator, path_spec):
    """Processes a path specification.

    Args:
      extraction_worker (worker.ExtractionWorker): extraction worker.
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification.
    """
    self._current_display_name = parser_mediator.GetDisplayNameForPathSpec(
        path_spec)

    self._CacheFileSystem(path_spec)

    excluded_find_specs = None
    if self.collection_filters_helper:
      excluded_find_specs = (
          self.collection_filters_helper.excluded_file_system_find_specs)

    try:
      extraction_worker.ProcessPathSpec(
          parser_mediator, path_spec, excluded_find_specs=excluded_find_specs)

    except KeyboardInterrupt:
      self._abort = True

      self._processing_status.aborted = True
      if self._status_update_callback:
        self._status_update_callback(self._processing_status)

    # We cannot recover from a CacheFullError and abort processing when
    # it is raised.
    except dfvfs_errors.CacheFullError:
      # TODO: signal engine of failure.
      self._abort = True
      logger.error((
          'ABORT: detected cache full error while processing '
          'path spec: {0:s}').format(self._current_display_name))

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

  def _ProcessSources(self, source_path_specs, parser_mediator):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      parser_mediator (ParserMediator): parser mediator.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('process_sources')

    self._status = definitions.STATUS_INDICATOR_COLLECTING
    self._current_display_name = ''
    self._number_of_consumed_sources = 0

    find_specs = None
    if self.collection_filters_helper:
      find_specs = (
          self.collection_filters_helper.included_file_system_find_specs)

    path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=find_specs, recurse_file_system=False,
        resolver_context=parser_mediator.resolver_context)

    for path_spec in path_spec_generator:
      if self._abort:
        break

      self._status = definitions.STATUS_INDICATOR_COLLECTING
      self._current_display_name = parser_mediator.GetDisplayNameForPathSpec(
          path_spec)

      # TODO: determine if event sources should be DataStream or FileEntry
      # or both.
      event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
      self._storage_writer.AddAttributeContainer(event_source)

    self._status = definitions.STATUS_INDICATOR_RUNNING

    if self._processing_profiler:
      self._processing_profiler.StartTiming('get_event_source')

    event_source = self._storage_writer.GetFirstWrittenEventSource()

    if self._processing_profiler:
      self._processing_profiler.StopTiming('get_event_source')

    while event_source:
      if self._abort:
        break

      self._ProcessPathSpec(
          self._extraction_worker, parser_mediator, event_source.path_spec)

      self._number_of_consumed_sources += 1

      if self._processing_profiler:
        self._processing_profiler.StartTiming('get_event_source')

      event_source = self._storage_writer.GetNextWrittenEventSource()

      if self._processing_profiler:
        self._processing_profiler.StopTiming('get_event_source')

    if self._abort:
      self._status = definitions.STATUS_INDICATOR_ABORTED
    else:
      self._status = definitions.STATUS_INDICATOR_COMPLETED

    self._current_display_name = ''

    if self._processing_profiler:
      self._processing_profiler.StopTiming('process_sources')

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

      time.sleep(self._STATUS_UPDATE_INTERVAL)

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
        self._storage_writer.number_of_event_sources,
        0, self._storage_writer.number_of_events,
        0, 0,
        0, 0,
        0, self._storage_writer.number_of_extraction_warnings)

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

  def ProcessSources(
      self, session, source_path_specs, storage_writer, resolver_context,
      processing_configuration, force_parser=False,
      status_update_callback=None):
    """Processes the sources.

    Args:
      session (Session): session in which the sources are processed.
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      storage_writer (StorageWriter): storage writer for a session storage.
      resolver_context (dfvfs.Context): resolver context.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      force_parser (Optional[bool]): True if a specified parser should be forced
          to be used to extract events.
      status_update_callback (Optional[function]): callback function for status
          updates.

    Returns:
      ProcessingStatus: processing status.
    """
    self._resolver_context = resolver_context
    self._session = session

    parser_mediator = parsers_mediator.ParserMediator(
        session, self.knowledge_base,
        collection_filters_helper=self.collection_filters_helper,
        preferred_year=processing_configuration.preferred_year,
        resolver_context=resolver_context,
        temporary_directory=processing_configuration.temporary_directory)
    parser_mediator.SetStorageWriter(storage_writer)

    self._extraction_worker = worker.EventExtractionWorker(
        force_parser=force_parser, parser_filter_expression=(
            processing_configuration.parser_filter_expression))

    self._extraction_worker.SetExtractionConfiguration(
        processing_configuration.extraction)

    self._processing_configuration = processing_configuration
    self._status_update_callback = status_update_callback
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

    try:
      self._ProcessSources(source_path_specs, parser_mediator)

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

    if self._abort:
      logger.debug('Processing aborted.')
      self._processing_status.aborted = True
    else:
      logger.debug('Processing completed.')

    # Update the status view one last time.
    self._UpdateStatus()

    self._extraction_worker = None
    self._file_system_cache = []
    self._processing_configuration = None
    self._resolver_context = None
    self._session = None
    self._status_update_callback = None
    self._storage_writer = None

    return self._processing_status
