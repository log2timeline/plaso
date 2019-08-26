# -*- coding: utf-8 -*-
"""The task multi-process processing engine."""

from __future__ import unicode_literals

import heapq
import logging
import multiprocessing
import os
import time

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context

from plaso.containers import event_sources
from plaso.containers import warnings
from plaso.engine import extractors
from plaso.engine import plaso_queue
from plaso.engine import zeromq_queue
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import loggers
from plaso.multi_processing import engine
from plaso.multi_processing import logger
from plaso.multi_processing import task_manager
from plaso.multi_processing import worker_process


class _EventSourceHeap(object):
  """Class that defines an event source heap."""

  def __init__(self, maximum_number_of_items=50000):
    """Initializes an event source heap.

    Args:
      maximum_number_of_items (Optional[int]): maximum number of items
          in the heap.
    """
    super(_EventSourceHeap, self).__init__()
    self._heap = []
    self._maximum_number_of_items = maximum_number_of_items

  def IsFull(self):
    """Determines if the heap is full.

    Returns:
      bool: True if the heap is full, False otherwise.
    """
    return len(self._heap) >= self._maximum_number_of_items

  def PopEventSource(self):
    """Pops an event source from the heap.

    Returns:
      EventSource: an event source or None on if no event source is available.
    """
    try:
      _, _, event_source = heapq.heappop(self._heap)

    except IndexError:
      return None

    return event_source

  def PushEventSource(self, event_source):
    """Pushes an event source onto the heap.

    Args:
      event_source (EventSource): event source.
    """
    if event_source.file_entry_type == (
        dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY):
      weight = 1
    else:
      weight = 100

    heap_values = (weight, time.time(), event_source)
    heapq.heappush(self._heap, heap_values)


class TaskMultiProcessEngine(engine.MultiProcessEngine):
  """Class that defines the task multi-process engine.

  This class contains functionality to:
  * monitor and manage extraction tasks;
  * merge results returned by extraction workers.
  """

  # Maximum number of attribute containers to merge per loop.
  _MAXIMUM_NUMBER_OF_CONTAINERS = 50

  # Maximum number of concurrent tasks.
  _MAXIMUM_NUMBER_OF_TASKS = 10000

  # Consider a worker inactive after 15 minutes of no activity.
  _PROCESS_WORKER_TIMEOUT = 15.0 * 60.0

  _WORKER_PROCESSES_MINIMUM = 2
  _WORKER_PROCESSES_MAXIMUM = 15

  _TASK_QUEUE_TIMEOUT_SECONDS = 2

  _ZEROMQ_NO_WORKER_REQUEST_TIME_SECONDS = 10 * 60

  def __init__(
      self, maximum_number_of_tasks=_MAXIMUM_NUMBER_OF_TASKS):
    """Initializes an engine.

    Args:
      maximum_number_of_tasks (Optional[int]): maximum number of concurrent
          tasks, where 0 represents no limit.
    """
    super(TaskMultiProcessEngine, self).__init__()
    self._enable_sigsegv_handler = False
    self._last_worker_number = 0
    self._maximum_number_of_tasks = maximum_number_of_tasks
    self._merge_task = None
    self._merge_task_on_hold = None
    self._number_of_consumed_event_tags = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_reports = 0
    self._number_of_consumed_sources = 0
    self._number_of_consumed_warnings = 0
    self._number_of_produced_event_tags = 0
    self._number_of_produced_events = 0
    self._number_of_produced_reports = 0
    self._number_of_produced_sources = 0
    self._number_of_produced_warnings = 0
    self._number_of_worker_processes = 0
    self._path_spec_extractor = extractors.PathSpecExtractor()
    self._processing_configuration = None
    self._resolver_context = context.Context()
    self._session_identifier = None
    self._status = definitions.STATUS_INDICATOR_IDLE
    self._storage_merge_reader = None
    self._storage_merge_reader_on_hold = None
    self._task_queue = None
    self._task_queue_port = None
    self._task_manager = task_manager.TaskManager()

  def _FillEventSourceHeap(
      self, storage_writer, event_source_heap, start_with_first=False):
    """Fills the event source heap with the available written event sources.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      event_source_heap (_EventSourceHeap): event source heap.
      start_with_first (Optional[bool]): True if the function should start
          with the first written event source.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('fill_event_source_heap')

    if self._processing_profiler:
      self._processing_profiler.StartTiming('get_event_source')

    if start_with_first:
      event_source = storage_writer.GetFirstWrittenEventSource()
    else:
      event_source = storage_writer.GetNextWrittenEventSource()

    if self._processing_profiler:
      self._processing_profiler.StopTiming('get_event_source')

    while event_source:
      event_source_heap.PushEventSource(event_source)
      if event_source_heap.IsFull():
        break

      if self._processing_profiler:
        self._processing_profiler.StartTiming('get_event_source')

      event_source = storage_writer.GetNextWrittenEventSource()

      if self._processing_profiler:
        self._processing_profiler.StopTiming('get_event_source')

    if self._processing_profiler:
      self._processing_profiler.StopTiming('fill_event_source_heap')

  def _MergeTaskStorage(self, storage_writer):
    """Merges a task storage with the session storage.

    This function checks all task stores that are ready to merge and updates
    the scheduled tasks. Note that to prevent this function holding up
    the task scheduling loop only the first available task storage is merged.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage used
          to merge task storage.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('merge_check')

    for task_identifier in storage_writer.GetProcessedTaskIdentifiers():
      try:
        task = self._task_manager.GetProcessedTaskByIdentifier(task_identifier)

        self._task_manager.SampleTaskStatus(task, 'processed')

        to_merge = self._task_manager.CheckTaskToMerge(task)
        if not to_merge:
          storage_writer.RemoveProcessedTaskStorage(task)

          self._task_manager.RemoveTask(task)
          self._task_manager.SampleTaskStatus(task, 'removed_processed')

        else:
          storage_writer.PrepareMergeTaskStorage(task)
          self._task_manager.UpdateTaskAsPendingMerge(task)

      except KeyError as exception:
        logger.error(
            'Unable to retrieve task: {0:s} to prepare it to be merged '
            'with error: {1!s}.'.format(task_identifier, exception))
        continue

    if self._processing_profiler:
      self._processing_profiler.StopTiming('merge_check')

    task = None
    if not self._storage_merge_reader_on_hold:
      task = self._task_manager.GetTaskPendingMerge(self._merge_task)

    # Limit the number of attribute containers from a single task-based
    # storage file that are merged per loop to keep tasks flowing.
    if task or self._storage_merge_reader:
      self._status = definitions.STATUS_INDICATOR_MERGING

      if self._processing_profiler:
        self._processing_profiler.StartTiming('merge')

      if task:
        if self._storage_merge_reader:
          self._merge_task_on_hold = self._merge_task
          self._storage_merge_reader_on_hold = self._storage_merge_reader

          self._task_manager.SampleTaskStatus(
              self._merge_task_on_hold, 'merge_on_hold')

        self._merge_task = task
        try:
          self._storage_merge_reader = storage_writer.StartMergeTaskStorage(
              task)

          self._task_manager.SampleTaskStatus(task, 'merge_started')

        except IOError as exception:
          logger.error((
              'Unable to merge results of task: {0:s} '
              'with error: {1!s}').format(task.identifier, exception))
          self._storage_merge_reader = None

      if self._storage_merge_reader:
        fully_merged = self._storage_merge_reader.MergeAttributeContainers(
            maximum_number_of_containers=self._MAXIMUM_NUMBER_OF_CONTAINERS)
      else:
        # TODO: Do something more sensible when this happens, perhaps
        # retrying the task once that is implemented. For now, we mark the task
        # as fully merged because we can't continue with it.
        fully_merged = True

      if self._processing_profiler:
        self._processing_profiler.StopTiming('merge')

      if fully_merged:
        try:
          self._task_manager.CompleteTask(self._merge_task)

        except KeyError as exception:
          logger.error(
              'Unable to complete task: {0:s} with error: {1!s}'.format(
                  self._merge_task.identifier, exception))

        if not self._storage_merge_reader_on_hold:
          self._merge_task = None
          self._storage_merge_reader = None
        else:
          self._merge_task = self._merge_task_on_hold
          self._storage_merge_reader = self._storage_merge_reader_on_hold

          self._merge_task_on_hold = None
          self._storage_merge_reader_on_hold = None

          self._task_manager.SampleTaskStatus(
              self._merge_task, 'merge_resumed')

      self._status = definitions.STATUS_INDICATOR_RUNNING
      self._number_of_produced_events = storage_writer.number_of_events
      self._number_of_produced_sources = storage_writer.number_of_event_sources
      self._number_of_produced_warnings = storage_writer.number_of_warnings

  def _ProcessSources(
      self, source_path_specs, storage_writer):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      storage_writer (StorageWriter): storage writer for a session storage.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('process_sources')

    self._status = definitions.STATUS_INDICATOR_COLLECTING
    self._number_of_consumed_event_tags = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_reports = 0
    self._number_of_consumed_sources = 0
    self._number_of_consumed_warnings = 0
    self._number_of_produced_event_tags = 0
    self._number_of_produced_events = 0
    self._number_of_produced_reports = 0
    self._number_of_produced_sources = 0
    self._number_of_produced_warnings = 0

    find_specs = None
    if self.collection_filters_helper:
      find_specs = (
          self.collection_filters_helper.included_file_system_find_specs)

    path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=find_specs, recurse_file_system=False,
        resolver_context=self._resolver_context)

    for path_spec in path_spec_generator:
      if self._abort:
        break

      # TODO: determine if event sources should be DataStream or FileEntry
      # or both.
      event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
      storage_writer.AddEventSource(event_source)

      self._number_of_produced_sources = storage_writer.number_of_event_sources

      # Update the foreman process status in case we are using a filter file.
      self._UpdateForemanProcessStatus()

      if self._status_update_callback:
        self._status_update_callback(self._processing_status)

    self._ScheduleTasks(storage_writer)

    if self._abort:
      self._status = definitions.STATUS_INDICATOR_ABORTED
    else:
      self._status = definitions.STATUS_INDICATOR_COMPLETED

    self._number_of_produced_events = storage_writer.number_of_events
    self._number_of_produced_sources = storage_writer.number_of_event_sources
    self._number_of_produced_warnings = storage_writer.number_of_warnings

    if self._processing_profiler:
      self._processing_profiler.StopTiming('process_sources')

    # Update the foreman process and task status in case we are using
    # a filter file.
    self._UpdateForemanProcessStatus()

    tasks_status = self._task_manager.GetStatusInformation()
    if self._task_queue_profiler:
      self._task_queue_profiler.Sample(tasks_status)

    self._processing_status.UpdateTasksStatus(tasks_status)

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

  def _ScheduleTask(self, task):
    """Schedules a task.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task was scheduled.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('schedule_task')

    try:
      self._task_queue.PushItem(task, block=False)
      is_scheduled = True

    except errors.QueueFull:
      is_scheduled = False

    if self._processing_profiler:
      self._processing_profiler.StopTiming('schedule_task')

    return is_scheduled

  def _ScheduleTasks(self, storage_writer):
    """Schedules tasks.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
    """
    logger.debug('Task scheduler started')

    self._status = definitions.STATUS_INDICATOR_RUNNING

    # TODO: make tasks persistent.

    # TODO: protect task scheduler loop by catch all and
    # handle abort path.

    event_source_heap = _EventSourceHeap()

    self._FillEventSourceHeap(
        storage_writer, event_source_heap, start_with_first=True)

    event_source = event_source_heap.PopEventSource()

    task = None
    while event_source or self._task_manager.HasPendingTasks():
      if self._abort:
        break

      try:
        if not task:
          task = self._task_manager.CreateRetryTask()

        if not task and event_source:
          task = self._task_manager.CreateTask(
              self._session_identifier,
              storage_format=self._processing_configuration.task_storage_format)
          task.file_entry_type = event_source.file_entry_type
          task.path_spec = event_source.path_spec
          event_source = None

          self._number_of_consumed_sources += 1

        if task:
          if self._ScheduleTask(task):
            task_path_spec_string = task.path_spec.comparable.replace('\n', ' ')
            logger.debug(
                'Scheduled task {0:s} for path specification {1:s}'.format(
                    task.identifier, task_path_spec_string))

            self._task_manager.SampleTaskStatus(task, 'scheduled')

            task = None

          else:
            self._task_manager.SampleTaskStatus(task, 'schedule_attempted')

        self._MergeTaskStorage(storage_writer)

        if not event_source_heap.IsFull():
          self._FillEventSourceHeap(storage_writer, event_source_heap)
        else:
          logger.debug('Source heap is full.')

        if not task and not event_source:
          event_source = event_source_heap.PopEventSource()

      except KeyboardInterrupt:
        self._abort = True

        self._processing_status.aborted = True
        if self._status_update_callback:
          self._status_update_callback(self._processing_status)

    for task in self._task_manager.GetFailedTasks():
      warning = warnings.ExtractionWarning(
          message='Worker failed to process path specification',
          path_spec=task.path_spec)
      self._storage_writer.AddWarning(warning)
      self._processing_status.error_path_specs.append(task.path_spec)

    self._status = definitions.STATUS_INDICATOR_IDLE

    if self._abort:
      logger.debug('Task scheduler aborted')
    else:
      logger.debug('Task scheduler stopped')

  def _StartWorkerProcess(self, process_name, storage_writer):
    """Creates, starts, monitors and registers a worker process.

    Args:
      process_name (str): process name.
      storage_writer (StorageWriter): storage writer for a session storage used
          to create task storage.

    Returns:
      MultiProcessWorkerProcess: extraction worker process or None if the
          process could not be started.
    """
    process_name = 'Worker_{0:02d}'.format(self._last_worker_number)
    logger.debug('Starting worker process {0:s}'.format(process_name))

    queue_name = '{0:s} task queue'.format(process_name)
    task_queue = zeromq_queue.ZeroMQRequestConnectQueue(
        delay_open=True, linger_seconds=0, name=queue_name,
        port=self._task_queue_port,
        timeout_seconds=self._TASK_QUEUE_TIMEOUT_SECONDS)

    process = worker_process.WorkerProcess(
        task_queue, storage_writer, self.collection_filters_helper,
        self.knowledge_base, self._session_identifier,
        self._processing_configuration,
        enable_sigsegv_handler=self._enable_sigsegv_handler, name=process_name)

    # Remove all possible log handlers to prevent a child process from logging
    # to the main process log file and garbling the log. The log handlers are
    # recreated after the worker process has been started.
    for handler in logging.root.handlers:
      logging.root.removeHandler(handler)
      handler.close()

    process.start()

    loggers.ConfigureLogging(
        debug_output=self._debug_output, filename=self._log_filename,
        mode='a', quiet_mode=self._quiet_mode)

    try:
      self._StartMonitoringProcess(process)

    except (IOError, KeyError) as exception:
      pid = process.pid
      logger.error((
          'Unable to monitor replacement worker process: {0:s} '
          '(PID: {1:d}) with error: {2!s}').format(
              process_name, pid, exception))

      self._TerminateProcess(process)
      return None

    self._RegisterProcess(process)

    self._last_worker_number += 1

    return process

  def _StatusUpdateThreadMain(self):
    """Main function of the status update thread."""
    while self._status_update_active:
      # Make a local copy of the PIDs in case the dict is changed by
      # the main thread.
      for pid in list(self._process_information_per_pid.keys()):
        self._CheckStatusWorkerProcess(pid)

      self._UpdateForemanProcessStatus()

      tasks_status = self._task_manager.GetStatusInformation()
      if self._task_queue_profiler:
        self._task_queue_profiler.Sample(tasks_status)

      self._processing_status.UpdateTasksStatus(tasks_status)

      if self._status_update_callback:
        self._status_update_callback(self._processing_status)

      time.sleep(self._STATUS_UPDATE_INTERVAL)

  def _StopExtractionProcesses(self, abort=False):
    """Stops the extraction processes.

    Args:
      abort (bool): True to indicated the stop is issued on abort.
    """
    logger.debug('Stopping extraction processes.')
    self._StopMonitoringProcesses()

    if abort:
      # Signal all the processes to abort.
      self._AbortTerminate()

    logger.debug('Emptying task queue.')
    self._task_queue.Empty()

    # Wake the processes to make sure that they are not blocking
    # waiting for the queue new items.
    for _ in self._processes_per_pid:
      try:
        self._task_queue.PushItem(plaso_queue.QueueAbort(), block=False)
      except errors.QueueFull:
        logger.warning('Task queue full, unable to push abort message.')

    # Try waiting for the processes to exit normally.
    self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)
    self._task_queue.Close(abort=abort)

    if not abort:
      # Check if the processes are still alive and terminate them if necessary.
      self._AbortTerminate()
      self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)
      self._task_queue.Close(abort=True)

    # Kill any lingering processes.
    self._AbortKill()

  def _UpdateForemanProcessStatus(self):
    """Update the foreman process status."""
    used_memory = self._process_information.GetUsedMemory() or 0

    if self._memory_profiler:
      self._memory_profiler.Sample('main', used_memory)

    display_name = getattr(self._merge_task, 'identifier', '')

    self._processing_status.UpdateForemanStatus(
        self._name, self._status, self._pid, used_memory, display_name,
        self._number_of_consumed_sources, self._number_of_produced_sources,
        self._number_of_consumed_events, self._number_of_produced_events,
        self._number_of_consumed_event_tags,
        self._number_of_produced_event_tags, self._number_of_consumed_reports,
        self._number_of_produced_reports, self._number_of_consumed_warnings,
        self._number_of_produced_warnings)

  def _UpdateProcessingStatus(self, pid, process_status, used_memory):
    """Updates the processing status.

    Args:
      pid (int): process identifier (PID) of the worker process.
      process_status (dict[str, object]): status values received from
          the worker process.
      used_memory (int): size of used memory in bytes.

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    self._RaiseIfNotRegistered(pid)

    if not process_status:
      return

    process = self._processes_per_pid[pid]

    processing_status = process_status.get('processing_status', None)

    self._RaiseIfNotMonitored(pid)

    display_name = process_status.get('display_name', '')

    number_of_consumed_event_tags = process_status.get(
        'number_of_consumed_event_tags', None)
    number_of_produced_event_tags = process_status.get(
        'number_of_produced_event_tags', None)

    number_of_consumed_events = process_status.get(
        'number_of_consumed_events', None)
    number_of_produced_events = process_status.get(
        'number_of_produced_events', None)

    number_of_consumed_reports = process_status.get(
        'number_of_consumed_reports', None)
    number_of_produced_reports = process_status.get(
        'number_of_produced_reports', None)

    number_of_consumed_sources = process_status.get(
        'number_of_consumed_sources', None)
    number_of_produced_sources = process_status.get(
        'number_of_produced_sources', None)

    number_of_consumed_warnings = process_status.get(
        'number_of_consumed_warnings', None)
    number_of_produced_warnings = process_status.get(
        'number_of_produced_warnings', None)

    if processing_status != definitions.STATUS_INDICATOR_IDLE:
      last_activity_timestamp = process_status.get(
          'last_activity_timestamp', 0.0)

      if last_activity_timestamp:
        last_activity_timestamp += self._PROCESS_WORKER_TIMEOUT

        current_timestamp = time.time()
        if current_timestamp > last_activity_timestamp:
          logger.error((
              'Process {0:s} (PID: {1:d}) has not reported activity within '
              'the timeout period.').format(process.name, pid))
          processing_status = definitions.STATUS_INDICATOR_NOT_RESPONDING

    self._processing_status.UpdateWorkerStatus(
        process.name, processing_status, pid, used_memory, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events,
        number_of_consumed_event_tags, number_of_produced_event_tags,
        number_of_consumed_reports, number_of_produced_reports,
        number_of_consumed_warnings, number_of_produced_warnings)

    task_identifier = process_status.get('task_identifier', '')
    if not task_identifier:
      return

    try:
      self._task_manager.UpdateTaskAsProcessingByIdentifier(task_identifier)
      return
    except KeyError:
      logger.debug(
          'Worker {0:s} is processing unknown task: {1:s}.'.format(
              process.name, task_identifier))

  def ProcessSources(
      self, session_identifier, source_path_specs, storage_writer,
      processing_configuration, enable_sigsegv_handler=False,
      number_of_worker_processes=0, status_update_callback=None,
      worker_memory_limit=None):
    """Processes the sources and extract events.

    Args:
      session_identifier (str): identifier of the session.
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      storage_writer (StorageWriter): storage writer for a session storage.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      enable_sigsegv_handler (Optional[bool]): True if the SIGSEGV handler
          should be enabled.
      number_of_worker_processes (Optional[int]): number of worker processes.
      status_update_callback (Optional[function]): callback function for status
          updates.
      worker_memory_limit (Optional[int]): maximum amount of memory a worker is
          allowed to consume, where None represents the default memory limit
          and 0 represents no limit.

    Returns:
      ProcessingStatus: processing status.
    """
    if number_of_worker_processes < 1:
      # One worker for each "available" CPU (minus other processes).
      # The number here is derived from the fact that the engine starts up:
      # * A main process.
      #
      # If we want to utilize all CPUs on the system we therefore need to start
      # up workers that amounts to the total number of CPUs - the other
      # processes.
      try:
        cpu_count = multiprocessing.cpu_count() - 1

        if cpu_count <= self._WORKER_PROCESSES_MINIMUM:
          cpu_count = self._WORKER_PROCESSES_MINIMUM

        elif cpu_count >= self._WORKER_PROCESSES_MAXIMUM:
          cpu_count = self._WORKER_PROCESSES_MAXIMUM

      except NotImplementedError:
        logger.error((
            'Unable to determine number of CPUs defaulting to {0:d} worker '
            'processes.').format(self._WORKER_PROCESSES_MINIMUM))
        cpu_count = self._WORKER_PROCESSES_MINIMUM

      number_of_worker_processes = cpu_count

    self._enable_sigsegv_handler = enable_sigsegv_handler
    self._number_of_worker_processes = number_of_worker_processes

    if worker_memory_limit is None:
      self._worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT
    else:
      self._worker_memory_limit = worker_memory_limit

    # Keep track of certain values so we can spawn new extraction workers.
    self._processing_configuration = processing_configuration

    self._debug_output = processing_configuration.debug_output
    self._log_filename = processing_configuration.log_filename
    self._session_identifier = session_identifier
    self._status_update_callback = status_update_callback
    self._storage_writer = storage_writer

    # Set up the task queue.
    task_outbound_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
        delay_open=True, linger_seconds=0, maximum_items=1,
        name='main_task_queue',
        timeout_seconds=self._ZEROMQ_NO_WORKER_REQUEST_TIME_SECONDS)
    self._task_queue = task_outbound_queue

    # The ZeroMQ backed queue must be started first, so we can save its port.
    # TODO: raises: attribute-defined-outside-init
    # self._task_queue.name = 'Task queue'
    self._task_queue.Open()
    self._task_queue_port = self._task_queue.port

    self._StartProfiling(self._processing_configuration.profiling)
    self._task_manager.StartProfiling(
        self._processing_configuration.profiling, self._name)

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      storage_writer.SetStorageProfiler(self._storage_profiler)

    # Set up the storage writer before the worker processes.
    storage_writer.StartTaskStorage()

    for worker_number in range(number_of_worker_processes):
      # First argument to _StartWorkerProcess is not used.
      extraction_process = self._StartWorkerProcess('', storage_writer)
      if not extraction_process:
        logger.error('Unable to create worker process: {0:d}'.format(
            worker_number))

    self._StartStatusUpdateThread()

    try:
      # Open the storage file after creating the worker processes otherwise
      # the ZIP storage file will remain locked as long as the worker processes
      # are alive.
      storage_writer.Open()
      storage_writer.WriteSessionStart()

      try:
        storage_writer.WritePreprocessingInformation(self.knowledge_base)

        self._ProcessSources(source_path_specs, storage_writer)

      finally:
        storage_writer.WriteSessionCompletion(aborted=self._abort)

        storage_writer.Close()

    finally:
      # Stop the status update thread after close of the storage writer
      # so we include the storage sync to disk in the status updates.
      self._StopStatusUpdateThread()

      if self._serializers_profiler:
        storage_writer.SetSerializersProfiler(None)

      if self._storage_profiler:
        storage_writer.SetStorageProfiler(None)

      self._task_manager.StopProfiling()
      self._StopProfiling()

    try:
      self._StopExtractionProcesses(abort=self._abort)

    except KeyboardInterrupt:
      self._AbortKill()

      # The abort can leave the main process unresponsive
      # due to incorrectly finalized IPC.
      self._KillProcess(os.getpid())

    # The task queue should be closed by _StopExtractionProcesses, this
    # close is a failsafe.
    self._task_queue.Close(abort=True)

    if self._processing_status.error_path_specs:
      task_storage_abort = True
    else:
      task_storage_abort = self._abort

    try:
      storage_writer.StopTaskStorage(abort=task_storage_abort)
    except (IOError, OSError) as exception:
      logger.error('Unable to stop task storage with error: {0!s}'.format(
          exception))

    if self._abort:
      logger.debug('Processing aborted.')
      self._processing_status.aborted = True
    else:
      logger.debug('Processing completed.')

    # Reset values.
    self._enable_sigsegv_handler = None
    self._number_of_worker_processes = None
    self._worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT

    self._processing_configuration = None

    self._session_identifier = None
    self._status_update_callback = None
    self._storage_writer = None

    return self._processing_status
