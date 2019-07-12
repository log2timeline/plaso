# -*- coding: utf-8 -*-
"""The multi-process worker process."""

from __future__ import unicode_literals

from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import context
from dfvfs.resolver import resolver

from plaso.engine import plaso_queue
from plaso.engine import worker
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import base_process
from plaso.multi_processing import logger
from plaso.parsers import mediator as parsers_mediator


class WorkerProcess(base_process.MultiProcessBaseProcess):
  """Class that defines a multi-processing worker process."""

  def __init__(
      self, task_queue, storage_writer, collection_filters_helper,
      knowledge_base, session_identifier, processing_configuration, **kwargs):
    """Initializes a worker process.

    Non-specified keyword arguments (kwargs) are directly passed to
    multiprocessing.Process.

    Args:
      task_queue (PlasoQueue): task queue.
      storage_writer (StorageWriter): storage writer for a session store.
      collection_filters_helper (CollectionFiltersHelper): collection filters
          helper.
      knowledge_base (KnowledgeBase): knowledge base which contains
          information from the source data needed for parsing.
      session_identifier (str): identifier of the session.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(WorkerProcess, self).__init__(processing_configuration, **kwargs)
    self._abort = False
    self._collection_filters_helper = collection_filters_helper
    self._buffer_size = 0
    self._current_display_name = ''
    self._extraction_worker = None
    self._knowledge_base = knowledge_base
    self._number_of_consumed_events = 0
    self._number_of_consumed_sources = 0
    self._parser_mediator = None
    self._session_identifier = session_identifier
    self._status = definitions.STATUS_INDICATOR_INITIALIZED
    self._storage_writer = storage_writer
    self._task = None
    self._task_queue = task_queue

  def _GetStatus(self):
    """Retrieves status information.

    Returns:
      dict[str, object]: status attributes, indexed by name.
    """
    if self._parser_mediator:
      number_of_produced_events = (
          self._parser_mediator.number_of_produced_events)
      number_of_produced_sources = (
          self._parser_mediator.number_of_produced_event_sources)
      number_of_produced_warnings = (
          self._parser_mediator.number_of_produced_warnings)
    else:
      number_of_produced_events = None
      number_of_produced_sources = None
      number_of_produced_warnings = None

    if self._extraction_worker and self._parser_mediator:
      last_activity_timestamp = max(
          self._extraction_worker.last_activity_timestamp,
          self._parser_mediator.last_activity_timestamp)
      processing_status = self._extraction_worker.processing_status
    else:
      last_activity_timestamp = 0.0
      processing_status = self._status

    task_identifier = getattr(self._task, 'identifier', '')

    if self._process_information:
      used_memory = self._process_information.GetUsedMemory() or 0
    else:
      used_memory = 0

    if self._memory_profiler:
      self._memory_profiler.Sample('main', used_memory)

    # XML RPC does not support integer values > 2 GiB so we format them
    # as a string.
    used_memory = '{0:d}'.format(used_memory)

    status = {
        'display_name': self._current_display_name,
        'identifier': self._name,
        'last_activity_timestamp': last_activity_timestamp,
        'number_of_consumed_event_tags': None,
        'number_of_consumed_events': self._number_of_consumed_events,
        'number_of_consumed_sources': self._number_of_consumed_sources,
        'number_of_consumed_warnings': None,
        'number_of_produced_event_tags': None,
        'number_of_produced_events': number_of_produced_events,
        'number_of_produced_sources': number_of_produced_sources,
        'number_of_produced_warnings': number_of_produced_warnings,
        'processing_status': processing_status,
        'task_identifier': task_identifier,
        'used_memory': used_memory}

    return status

  def _Main(self):
    """The main loop."""
    # We need a resolver context per process to prevent multi processing
    # issues with file objects stored in images.
    resolver_context = context.Context()

    for credential_configuration in self._processing_configuration.credentials:
      resolver.Resolver.key_chain.SetCredential(
          credential_configuration.path_spec,
          credential_configuration.credential_type,
          credential_configuration.credential_data)

    self._parser_mediator = parsers_mediator.ParserMediator(
        None, self._knowledge_base,
        collection_filters_helper=self._collection_filters_helper,
        preferred_year=self._processing_configuration.preferred_year,
        resolver_context=resolver_context,
        temporary_directory=self._processing_configuration.temporary_directory)

    self._parser_mediator.SetEventExtractionConfiguration(
        self._processing_configuration.event_extraction)

    self._parser_mediator.SetInputSourceConfiguration(
        self._processing_configuration.input_source)

    # We need to initialize the parser and hasher objects after the process
    # has forked otherwise on Windows the "fork" will fail with
    # a PickleError for Python modules that cannot be pickled.
    self._extraction_worker = worker.EventExtractionWorker(
        parser_filter_expression=(
            self._processing_configuration.parser_filter_expression))

    self._extraction_worker.SetExtractionConfiguration(
        self._processing_configuration.extraction)

    self._parser_mediator.StartProfiling(
        self._processing_configuration.profiling, self._name,
        self._process_information)
    self._StartProfiling(self._processing_configuration.profiling)

    if self._processing_profiler:
      self._extraction_worker.SetProcessingProfiler(self._processing_profiler)

    if self._serializers_profiler:
      self._storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._storage_writer.SetStorageProfiler(self._storage_profiler)

    logger.debug('Worker: {0!s} (PID: {1:d}) started.'.format(
        self._name, self._pid))

    self._status = definitions.STATUS_INDICATOR_RUNNING

    try:
      logger.debug('{0!s} (PID: {1:d}) started monitoring task queue.'.format(
          self._name, self._pid))

      while not self._abort:
        try:
          task = self._task_queue.PopItem()
        except (errors.QueueClose, errors.QueueEmpty) as exception:
          logger.debug('ConsumeItems exiting with exception {0:s}.'.format(
              type(exception)))
          break

        if isinstance(task, plaso_queue.QueueAbort):
          logger.debug('ConsumeItems exiting, dequeued QueueAbort object.')
          break

        self._ProcessTask(task)

      logger.debug('{0!s} (PID: {1:d}) stopped monitoring task queue.'.format(
          self._name, self._pid))

    # All exceptions need to be caught here to prevent the process
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      logger.warning(
          'Unhandled exception in process: {0!s} (PID: {1:d}).'.format(
              self._name, self._pid))
      logger.exception(exception)

      self._abort = True

    if self._processing_profiler:
      self._extraction_worker.SetProcessingProfiler(None)

    if self._serializers_profiler:
      self._storage_writer.SetSerializersProfiler(None)

    if self._storage_profiler:
      self._storage_writer.SetStorageProfiler(None)

    self._StopProfiling()
    self._parser_mediator.StopProfiling()

    self._extraction_worker = None
    self._parser_mediator = None
    self._storage_writer = None

    if self._abort:
      self._status = definitions.STATUS_INDICATOR_ABORTED
    else:
      self._status = definitions.STATUS_INDICATOR_COMPLETED

    logger.debug('Worker: {0!s} (PID: {1:d}) stopped.'.format(
        self._name, self._pid))

    try:
      self._task_queue.Close(abort=self._abort)
    except errors.QueueAlreadyClosed:
      logger.error('Queue for {0:s} was already closed.'.format(self.name))

  def _ProcessPathSpec(self, extraction_worker, parser_mediator, path_spec):
    """Processes a path specification.

    Args:
      extraction_worker (worker.ExtractionWorker): extraction worker.
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification.
    """
    self._current_display_name = parser_mediator.GetDisplayNameForPathSpec(
        path_spec)

    excluded_find_specs = None
    if self._collection_filters_helper:
      excluded_find_specs = (
          self._collection_filters_helper.excluded_file_system_find_specs)

    try:
      extraction_worker.ProcessPathSpec(
          parser_mediator, path_spec, excluded_find_specs=excluded_find_specs)

    except dfvfs_errors.CacheFullError:
      # TODO: signal engine of failure.
      self._abort = True
      logger.error((
          'ABORT: detected cache full error while processing path spec: '
          '{0:s}').format(self._current_display_name))

    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionWarning((
          'unable to process path specification with error: '
          '{0!s}').format(exception), path_spec=path_spec)

      if self._processing_configuration.debug_output:
        logger.warning((
            'Unhandled exception while processing path specification: '
            '{0:s}.').format(self._current_display_name))
        logger.exception(exception)

  def _ProcessTask(self, task):
    """Processes a task.

    Args:
      task (Task): task.
    """
    logger.debug('Started processing task: {0:s}.'.format(task.identifier))

    if self._tasks_profiler:
      self._tasks_profiler.Sample(task, 'processing_started')

    self._task = task

    task_storage_writer = self._storage_writer.CreateTaskStorage(
        task, self._processing_configuration.task_storage_format)

    if self._serializers_profiler:
      task_storage_writer.SetSerializersProfiler(self._serializers_profiler)

    task_storage_writer.Open()

    self._parser_mediator.SetStorageWriter(task_storage_writer)

    task_storage_writer.WriteTaskStart()

    try:
      # TODO: add support for more task types.
      self._ProcessPathSpec(
          self._extraction_worker, self._parser_mediator, task.path_spec)
      self._number_of_consumed_sources += 1

    finally:
      task_storage_writer.WriteTaskCompletion(aborted=self._abort)

      self._parser_mediator.SetStorageWriter(None)

      task_storage_writer.Close()

    try:
      self._storage_writer.FinalizeTaskStorage(task)
    except IOError:
      pass

    self._task = None

    if self._tasks_profiler:
      self._tasks_profiler.Sample(task, 'processing_completed')

    logger.debug('Completed processing task: {0:s}.'.format(task.identifier))

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
    if self._extraction_worker:
      self._extraction_worker.SignalAbort()
    if self._parser_mediator:
      self._parser_mediator.SignalAbort()
