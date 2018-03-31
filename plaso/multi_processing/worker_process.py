# -*- coding: utf-8 -*-
"""The multi-process worker process."""

from __future__ import unicode_literals

import os

from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import context
from dfvfs.resolver import resolver

from plaso.engine import plaso_queue
from plaso.engine import profiler
from plaso.engine import worker
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import base_process
from plaso.multi_processing import logger
from plaso.parsers import mediator as parsers_mediator


class WorkerProcess(base_process.MultiProcessBaseProcess):
  """Class that defines a multi-processing worker process."""

  def __init__(
      self, task_queue, storage_writer, knowledge_base, session_identifier,
      processing_configuration, **kwargs):
    """Initializes a worker process.

    Non-specified keyword arguments (kwargs) are directly passed to
    multiprocessing.Process.

    Args:
      task_queue (PlasoQueue): task queue.
      storage_writer (StorageWriter): storage writer for a session storage.
      knowledge_base (KnowledgeBase): knowledge base which contains
          information from the source data needed for parsing.
      session_identifier (str): identifier of the session.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(WorkerProcess, self).__init__(**kwargs)
    self._abort = False
    self._buffer_size = 0
    self._current_display_name = ''
    self._extraction_worker = None
    self._guppy_memory_profiler = None
    self._knowledge_base = knowledge_base
    self._memory_profiler = None
    self._number_of_consumed_events = 0
    self._number_of_consumed_sources = 0
    self._parser_mediator = None
    self._parsers_profiler = None
    self._processing_configuration = processing_configuration
    self._processing_profiler = None
    self._serializers_profiler = None
    self._session_identifier = session_identifier
    self._status = definitions.PROCESSING_STATUS_INITIALIZED
    self._storage_profiler = None
    self._storage_writer = storage_writer
    self._task = None
    self._task_queue = task_queue

    if self._processing_configuration:
      self._debug_output = self._processing_configuration.debug_output

      if processing_configuration.log_filename:
        log_path = os.path.dirname(self._processing_configuration.log_filename)
        log_filename = os.path.basename(
            self._processing_configuration.log_filename)
        log_filename = '{0:s}_{1:s}'.format(self._name, log_filename)
        self._log_filename = os.path.join(log_path, log_filename)

  def _GetStatus(self):
    """Retrieves status information.

    Returns:
      dict[str, object]: status attributes, indexed by name.
    """
    if self._parser_mediator:
      number_of_produced_errors = (
          self._parser_mediator.number_of_produced_errors)
      number_of_produced_events = (
          self._parser_mediator.number_of_produced_events)
      number_of_produced_sources = (
          self._parser_mediator.number_of_produced_event_sources)
    else:
      number_of_produced_errors = None
      number_of_produced_events = None
      number_of_produced_sources = None

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
      self._memory_profiler.Sample(used_memory)

    status = {
        'display_name': self._current_display_name,
        'identifier': self._name,
        'number_of_consumed_errors': None,
        'number_of_consumed_event_tags': None,
        'number_of_consumed_events': self._number_of_consumed_events,
        'number_of_consumed_sources': self._number_of_consumed_sources,
        'number_of_produced_errors': number_of_produced_errors,
        'number_of_produced_event_tags': None,
        'number_of_produced_events': number_of_produced_events,
        'number_of_produced_sources': number_of_produced_sources,
        'last_activity_timestamp': last_activity_timestamp,
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

    self._StartProfiling(self._processing_configuration.profiling)

    if self._parsers_profiler:
      self._extraction_worker.SetParsersProfiler(self._parsers_profiler)

    if self._processing_profiler:
      self._extraction_worker.SetProcessingProfiler(self._processing_profiler)

    if self._serializers_profiler:
      self._storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._storage_writer.SetStorageProfiler(self._storage_profiler)

    logger.debug('Worker: {0!s} (PID: {1:d}) started'.format(
        self._name, self._pid))

    self._status = definitions.PROCESSING_STATUS_RUNNING

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

    if self._parsers_profiler:
      self._extraction_worker.SetParsersProfiler(None)

    if self._processing_profiler:
      self._extraction_worker.SetProcessingProfiler(None)

    if self._serializers_profiler:
      self._storage_writer.SetSerializersProfiler(None)

    if self._storage_profiler:
      self._storage_writer.SetStorageProfiler(None)

    self._StopProfiling()

    self._extraction_worker = None
    self._parser_mediator = None
    self._storage_writer = None

    if self._abort:
      self._status = definitions.PROCESSING_STATUS_ABORTED
    else:
      self._status = definitions.PROCESSING_STATUS_COMPLETED

    logger.debug('Worker: {0!s} (PID: {1:d}) stopped'.format(
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

    try:
      extraction_worker.ProcessPathSpec(parser_mediator, path_spec)

    except dfvfs_errors.CacheFullError:
      # TODO: signal engine of failure.
      self._abort = True
      logger.error((
          'ABORT: detected cache full error while processing path spec: '
          '{0:s}').format(self._current_display_name))

    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionError((
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
    self._task = task

    storage_writer = self._storage_writer.CreateTaskStorage(task)

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    storage_writer.Open()

    self._parser_mediator.SetStorageWriter(storage_writer)

    storage_writer.WriteTaskStart()

    try:
      # TODO: add support for more task types.
      self._ProcessPathSpec(
          self._extraction_worker, self._parser_mediator, task.path_spec)
      self._number_of_consumed_sources += 1

      if self._guppy_memory_profiler:
        self._guppy_memory_profiler.Sample()

    finally:
      storage_writer.WriteTaskCompletion(aborted=self._abort)

      self._parser_mediator.SetStorageWriter(None)

      storage_writer.Close()

    try:
      self._storage_writer.PrepareMergeTaskStorage(task)
    except IOError:
      pass

    self._task = None

  def _StartProfiling(self, configuration):
    """Starts profiling.

    Args:
      configuration (ProfilingConfiguration): profiling configuration.
    """
    if not configuration:
      return

    if configuration.HaveProfileMemoryGuppy():
      self._guppy_memory_profiler = profiler.GuppyMemoryProfiler(
          self._name, configuration)
      self._guppy_memory_profiler.Start()

    if configuration.HaveProfileMemory():
      self._memory_profiler = profiler.MemoryProfiler(
          self._name, configuration)
      self._memory_profiler.Start()

    if configuration.HaveProfileParsers():
      identifier = '{0:s}-parsers'.format(self._name)
      self._parsers_profiler = profiler.ParsersProfiler(
          identifier, configuration)
      self._parsers_profiler.Start()

    if configuration.HaveProfileProcessing():
      identifier = '{0:s}-processing'.format(self._name)
      self._processing_profiler = profiler.ProcessingProfiler(
          identifier, configuration)
      self._processing_profiler.Start()

    if configuration.HaveProfileSerializers():
      identifier = '{0:s}-serializers'.format(self._name)
      self._serializers_profiler = profiler.SerializersProfiler(
          identifier, configuration)
      self._serializers_profiler.Start()

    if configuration.HaveProfileStorage():
      self._storage_profiler = profiler.StorageProfiler(
          self._name, configuration)
      self._storage_profiler.Start()

  def _StopProfiling(self):
    """Stops profiling."""
    if self._guppy_memory_profiler:
      self._guppy_memory_profiler.Sample()
      self._guppy_memory_profiler.Stop()
      self._guppy_memory_profiler = None

    if self._memory_profiler:
      self._memory_profiler.Stop()
      self._memory_profiler = None

    if self._parsers_profiler:
      self._parsers_profiler.Stop()
      self._parsers_profiler = None

    if self._processing_profiler:
      self._processing_profiler.Stop()
      self._processing_profiler = None

    if self._serializers_profiler:
      self._serializers_profiler.Stop()
      self._serializers_profiler = None

    if self._storage_profiler:
      self._storage_profiler.Stop()
      self._storage_profiler = None

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
    if self._extraction_worker:
      self._extraction_worker.SignalAbort()
    if self._parser_mediator:
      self._parser_mediator.SignalAbort()
