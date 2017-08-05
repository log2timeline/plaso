# -*- coding: utf-8 -*-
"""The task multi-process processing engine."""

import heapq
import logging
import multiprocessing
import os
import time

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context

from plaso.containers import event_sources
from plaso.containers import errors as error_containers
from plaso.engine import extractors
from plaso.engine import plaso_queue
from plaso.engine import profiler
from plaso.engine import zeromq_queue
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import engine
from plaso.multi_processing import multi_process_queue
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

  def PopEventSource(self):
    """Pops an event source from the heap.

    Returns:
      EventSource: event source.
    """
    try:
      _, event_source = heapq.heappop(self._heap)

    except IndexError:
      return

    return event_source

  def PushEventSource(self, event_source):
    """Pushes an event source onto the heap.

    Args:
      event_source (EventSource): event source.

    Raises:
      HeapFull: if the heap contains the maximum number of items. Note that
          this exception is raised after the item is added to the heap.
    """
    if event_source.file_entry_type == (
        dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY):
      weight = 1
    else:
      weight = 100

    heap_values = (weight, event_source)
    heapq.heappush(self._heap, heap_values)

    if len(self._heap) >= self._maximum_number_of_items:
      raise errors.HeapFull()


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

  _PROCESS_JOIN_TIMEOUT = 5.0
  _PROCESS_WORKER_TIMEOUT = 15.0 * 60.0

  _WORKER_PROCESSES_MINIMUM = 2
  _WORKER_PROCESSES_MAXIMUM = 15

  _TASK_QUEUE_TIMEOUT_SECONDS = 2

  _ZEROMQ_NO_WORKER_REQUEST_TIME_SECONDS = 10 * 60

  def __init__(
      self, maximum_number_of_tasks=_MAXIMUM_NUMBER_OF_TASKS, use_zeromq=True):
    """Initializes an engine object.

    Args:
      maximum_number_of_tasks (Optional[int]): maximum number of concurrent
          tasks, where 0 represents no limit.
      use_zeromq (Optional[bool]): True if ZeroMQ should be used for queuing
          instead of Python's multiprocessing queue.
    """
    super(TaskMultiProcessEngine, self).__init__()
    self._enable_sigsegv_handler = False
    self._filter_find_specs = None
    self._guppy_memory_profiler = None
    self._last_worker_number = 0
    self._maximum_number_of_tasks = maximum_number_of_tasks
    self._merge_task = None
    self._merge_task_on_hold = None
    self._number_of_consumed_errors = 0
    self._number_of_consumed_event_tags = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_reports = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_errors = 0
    self._number_of_produced_event_tags = 0
    self._number_of_produced_events = 0
    self._number_of_produced_reports = 0
    self._number_of_produced_sources = 0
    self._number_of_worker_processes = 0
    self._path_spec_extractor = extractors.PathSpecExtractor()
    self._processing_configuration = None
    self._processing_profiler = None
    self._resolver_context = context.Context()
    self._serializers_profiler = None
    self._session_identifier = None
    self._status = definitions.PROCESSING_STATUS_IDLE
    self._storage_merge_reader = None
    self._storage_merge_reader_on_hold = None
    self._task_queue = None
    self._task_queue_port = None
    self._task_manager = task_manager.TaskManager()
    self._use_zeromq = use_zeromq

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
      self._processing_profiler.StartTiming(u'fill_event_source_heap')

    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'get_event_source')

    if start_with_first:
      event_source = storage_writer.GetFirstWrittenEventSource()
    else:
      event_source = storage_writer.GetNextWrittenEventSource()

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'get_event_source')

    while event_source:
      try:
        event_source_heap.PushEventSource(event_source)
      except errors.HeapFull:
        break

      if self._processing_profiler:
        self._processing_profiler.StartTiming(u'get_event_source')

      event_source = storage_writer.GetNextWrittenEventSource()

      if self._processing_profiler:
        self._processing_profiler.StopTiming(u'get_event_source')

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'fill_event_source_heap')

  def _MergeTaskStorage(self, storage_writer):
    """Merges a task storage with the session storage.

    This function checks all task storages that are ready to merge and updates
    the scheduled tasks. Note that to prevent this function holding up
    the task scheduling loop only the first available task storage is merged.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage used
          to merge task storage.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'merge_check')

    for task in self._task_manager.GetTasksCheckMerge():
      if self._abort:
        break

      merge_ready = storage_writer.CheckTaskReadyForMerge(task)
      if merge_ready:
        self._task_manager.UpdateTaskAsPendingMerge(task)

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'merge_check')

    task = None
    if not self._storage_merge_reader_on_hold:
      task = self._task_manager.GetTaskPendingMerge(self._merge_task)

    # Limit the number of attribute containers from a single task-based
    # storage file that are merged per loop to keep tasks flowing.
    if task or self._storage_merge_reader:
      self._status = definitions.PROCESSING_STATUS_MERGING

      if self._processing_profiler:
        self._processing_profiler.StartTiming(u'merge')

      if task:
        if self._storage_merge_reader:
          self._merge_task_on_hold = self._merge_task
          self._storage_merge_reader_on_hold = self._storage_merge_reader

        self._merge_task = task
        try:
          self._storage_merge_reader = storage_writer.StartMergeTaskStorage(
              task)
        except IOError as exception:
          logging.error((
              u'Unable to merge results of task: {0:s} '
              u'with error: {1:s}').format(task.identifier, exception))
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
        self._processing_profiler.StopTiming(u'merge')

      if fully_merged:
        try:
          self._task_manager.CompleteTask(self._merge_task)
        except KeyError as exception:
          logging.error(
              u'Unable to complete task {0:s}, with Error {1:s}'.format(
                  self._merge_task.identifier, exception))

        if self._storage_merge_reader_on_hold:
          self._merge_task = self._merge_task_on_hold
          self._storage_merge_reader = self._storage_merge_reader_on_hold

          self._merge_task_on_hold = None
          self._storage_merge_reader_on_hold = None
        else:
          self._merge_task = None
          self._storage_merge_reader = None

      self._status = definitions.PROCESSING_STATUS_RUNNING
      self._number_of_produced_errors = storage_writer.number_of_errors
      self._number_of_produced_events = storage_writer.number_of_events
      self._number_of_produced_sources = storage_writer.number_of_event_sources

  def _ProcessSources(
      self, source_path_specs, storage_writer, filter_find_specs=None):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      storage_writer (StorageWriter): storage writer for a session storage.
      filter_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
          used in path specification extraction. If set, path specifications
          that match the find specification will be processed.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'process_sources')

    self._status = definitions.PROCESSING_STATUS_COLLECTING
    self._number_of_consumed_errors = 0
    self._number_of_consumed_event_tags = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_reports = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_errors = 0
    self._number_of_produced_event_tags = 0
    self._number_of_produced_events = 0
    self._number_of_produced_reports = 0
    self._number_of_produced_sources = 0

    path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=filter_find_specs,
        recurse_file_system=False, resolver_context=self._resolver_context)

    for path_spec in path_spec_generator:
      if self._abort:
        break

      # TODO: determine if event sources should be DataStream or FileEntry
      # or both.
      event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
      storage_writer.AddEventSource(event_source)

      self._number_of_produced_sources = storage_writer.number_of_event_sources

    self._ScheduleTasks(storage_writer)

    if self._abort:
      self._status = definitions.PROCESSING_STATUS_ABORTED
    else:
      self._status = definitions.PROCESSING_STATUS_COMPLETED

    self._number_of_produced_errors = storage_writer.number_of_errors
    self._number_of_produced_events = storage_writer.number_of_events
    self._number_of_produced_sources = storage_writer.number_of_event_sources

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'process_sources')

  def _ProfilingSampleMemory(self):
    """Creates a memory profiling sample."""
    if self._guppy_memory_profiler:
      self._guppy_memory_profiler.Sample()

  def _ScheduleTask(self, task):
    """Schedules a task.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task was scheduled.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'schedule_task')

    try:
      self._task_queue.PushItem(task, block=False)
      is_scheduled = True

    except errors.QueueFull:
      is_scheduled = False

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'schedule_task')

    return is_scheduled

  def _ScheduleTasks(self, storage_writer):
    """Schedules tasks.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
    """
    logging.debug(u'Task scheduler started')

    self._status = definitions.PROCESSING_STATUS_RUNNING

    # TODO: make tasks persistent.

    # TODO: protect task scheduler loop by catch all and
    # handle abort path.

    task = None

    event_source_heap = _EventSourceHeap()

    self._FillEventSourceHeap(
        storage_writer, event_source_heap, start_with_first=True)

    event_source = event_source_heap.PopEventSource()

    while event_source or self._task_manager.HasPendingTasks():
      if self._abort:
        break

      try:
        if not task:
          task = self._task_manager.GetRetryTask()
        if event_source and not task:
          task = self._task_manager.CreateTask(self._session_identifier)
          task.file_entry_type = event_source.file_entry_type
          task.path_spec = event_source.path_spec
          event_source = None

          self._number_of_consumed_sources += 1

          if self._guppy_memory_profiler:
            self._guppy_memory_profiler.Sample()

        if task:
          if self._ScheduleTask(task):
            logging.debug(
                u'Scheduled task {0:s} for path specification {1:s}'.format(
                    task.identifier, task.path_spec.comparable))
            task = None

        self._MergeTaskStorage(storage_writer)

        self._FillEventSourceHeap(storage_writer, event_source_heap)

        if not event_source and not task:
          event_source = event_source_heap.PopEventSource()

      except KeyboardInterrupt:
        self._abort = True

        self._processing_status.aborted = True
        if self._status_update_callback:
          self._status_update_callback(self._processing_status)

    for task in self._task_manager.GetAbandonedTasks():
      if not task.retried:
        error = error_containers.ExtractionError(
            message=u'Worker failed to process pathspec',
            path_spec=task.path_spec)
        self._storage_writer.AddError(error)
        self._processing_status.error_path_specs.append(task.path_spec)

    self._status = definitions.PROCESSING_STATUS_IDLE

    if self._abort:
      logging.debug(u'Task scheduler aborted')
    else:
      logging.debug(u'Task scheduler stopped')

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
    process_name = u'Worker_{0:02d}'.format(self._last_worker_number)
    logging.debug(u'Starting worker process {0:s}'.format(process_name))

    if self._use_zeromq:
      queue_name = u'{0:s} task queue'.format(process_name)
      task_queue = zeromq_queue.ZeroMQRequestConnectQueue(
          delay_open=True, linger_seconds=0, name=queue_name,
          port=self._task_queue_port,
          timeout_seconds=self._TASK_QUEUE_TIMEOUT_SECONDS)
    else:
      task_queue = self._task_queue

    process = worker_process.WorkerProcess(
        task_queue, storage_writer, self.knowledge_base,
        self._session_identifier, self._processing_configuration,
        enable_sigsegv_handler=self._enable_sigsegv_handler, name=process_name)

    process.start()

    try:
      self._StartMonitoringProcess(process)

    except (IOError, KeyError) as exception:
      logging.error((
          u'Unable to monitor replacement worker process: {0:s} '
          u'(PID: {1:d}) with error: {2:s}').format(
              process_name, process.pid, exception))

      process.terminate()
      return

    self._RegisterProcess(process)

    self._last_worker_number += 1

    return process

  def _StartProfiling(self):
    """Starts profiling."""
    if not self._processing_configuration:
      return

    if self._processing_configuration.profiling.HaveProfileMemoryGuppy():
      identifier = u'{0:s}-memory'.format(self._name)
      self._guppy_memory_profiler = profiler.GuppyMemoryProfiler(
          identifier, path=self._processing_configuration.profiling.directory,
          profiling_sample_rate=(
              self._processing_configuration.profiling.sample_rate))
      self._guppy_memory_profiler.Start()

    if self._processing_configuration.profiling.HaveProfileProcessing():
      identifier = u'{0:s}-processing'.format(self._name)
      self._processing_profiler = profiler.ProcessingProfiler(
          identifier, path=self._processing_configuration.profiling.directory)

    if self._processing_configuration.profiling.HaveProfileSerializers():
      identifier = u'{0:s}-serializers'.format(self._name)
      self._serializers_profiler = profiler.SerializersProfiler(
          identifier, path=self._processing_configuration.profiling.directory)

  def _StatusUpdateThreadMain(self):
    """Main function of the status update thread."""
    while self._status_update_active:
      # Make a local copy of the PIDs in case the dict is changed by
      # the main thread.
      for pid in list(self._process_information_per_pid.keys()):
        self._CheckStatusWorkerProcess(pid)

      used_memory = self._process_information.GetUsedMemory() or 0

      display_name = getattr(self._merge_task, u'identifier', u'')

      self._processing_status.UpdateForemanStatus(
          self._name, self._status, self._pid, used_memory, display_name,
          self._number_of_consumed_sources, self._number_of_produced_sources,
          self._number_of_consumed_events, self._number_of_produced_events,
          self._number_of_consumed_event_tags,
          self._number_of_produced_event_tags,
          self._number_of_consumed_errors, self._number_of_produced_errors,
          self._number_of_consumed_reports, self._number_of_produced_reports)

      tasks_status = self._task_manager.GetStatusInformation()
      self._processing_status.UpdateTasksStatus(tasks_status)

      if self._status_update_callback:
        self._status_update_callback(self._processing_status)

      time.sleep(self._STATUS_UPDATE_INTERVAL)

  def _StopExtractionProcesses(self, abort=False):
    """Stops the extraction processes.

    Args:
      abort (bool): True to indicated the stop is issued on abort.
    """
    logging.debug(u'Stopping extraction processes.')
    self._StopMonitoringProcesses()

    # Note that multiprocessing.Queue is very sensitive regarding
    # blocking on either a get or a put. So we try to prevent using
    # any blocking behavior.

    if abort:
      # Signal all the processes to abort.
      self._AbortTerminate()

    logging.debug(u'Emptying task queue.')
    self._task_queue.Empty()

    # Wake the processes to make sure that they are not blocking
    # waiting for the queue new items.
    for _ in range(self._number_of_worker_processes):
      try:
        self._task_queue.PushItem(plaso_queue.QueueAbort(), block=False)
      except errors.QueueFull:
        logging.warning(u'Task queue full, unable to push abort message.')

    # Try waiting for the processes to exit normally.
    self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)
    self._task_queue.Close(abort=abort)

    if abort:
      # Kill any remaining processes.
      self._AbortKill()
    else:
      # Check if the processes are still alive and terminate them if necessary.
      self._AbortTerminate()
      self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)

      self._task_queue.Close(abort=True)

  def _StopProfiling(self):
    """Stops profiling."""
    if self._guppy_memory_profiler:
      self._guppy_memory_profiler.Sample()
      self._guppy_memory_profiler = None

    if self._processing_profiler:
      self._processing_profiler.Write()
      self._processing_profiler = None

    if self._serializers_profiler:
      self._serializers_profiler.Write()
      self._serializers_profiler = None

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

    processing_status = process_status.get(u'processing_status', None)

    self._RaiseIfNotMonitored(pid)

    display_name = process_status.get(u'display_name', u'')
    number_of_consumed_errors = process_status.get(
        u'number_of_consumed_errors', None)
    number_of_produced_errors = process_status.get(
        u'number_of_produced_errors', None)

    number_of_consumed_event_tags = process_status.get(
        u'number_of_consumed_event_tags', None)
    number_of_produced_event_tags = process_status.get(
        u'number_of_produced_event_tags', None)

    number_of_consumed_events = process_status.get(
        u'number_of_consumed_events', None)
    number_of_produced_events = process_status.get(
        u'number_of_produced_events', None)

    number_of_consumed_reports = process_status.get(
        u'number_of_consumed_reports', None)
    number_of_produced_reports = process_status.get(
        u'number_of_produced_reports', None)

    number_of_consumed_sources = process_status.get(
        u'number_of_consumed_sources', None)
    number_of_produced_sources = process_status.get(
        u'number_of_produced_sources', None)

    if processing_status != definitions.PROCESSING_STATUS_IDLE:
      last_activity_timestamp = process_status.get(
          u'last_activity_timestamp', 0.0)

      if last_activity_timestamp:
        last_activity_timestamp += self._PROCESS_WORKER_TIMEOUT

        current_timestamp = time.time()
        if current_timestamp > last_activity_timestamp:
          logging.error((
              u'Process {0:s} (PID: {1:d}) has not reported activity within '
              u'the timeout period.').format(process.name, pid))
          processing_status = definitions.PROCESSING_STATUS_NOT_RESPONDING

    self._processing_status.UpdateWorkerStatus(
        process.name, processing_status, pid, used_memory, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events,
        number_of_consumed_event_tags, number_of_produced_event_tags,
        number_of_consumed_errors, number_of_produced_errors,
        number_of_consumed_reports, number_of_produced_reports)

    task_identifier = process_status.get(u'task_identifier', u'')
    if not task_identifier:
      return

    try:
      self._task_manager.UpdateTaskAsProcessingByIdentifier(task_identifier)
      return
    except KeyError:
      logging.debug(
          u'Worker {0:s} is processing unknown task: {1:s}.'.format(
              process.name, task_identifier))

  def ProcessSources(
      self, session_identifier, source_path_specs, storage_writer,
      processing_configuration, enable_sigsegv_handler=False,
      filter_find_specs=None, number_of_worker_processes=0,
      status_update_callback=None, worker_memory_limit=None):
    """Processes the sources and extract event objects.

    Args:
      session_identifier (str): identifier of the session.
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      storage_writer (StorageWriter): storage writer for a session storage.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      enable_sigsegv_handler (Optional[bool]): True if the SIGSEGV handler
          should be enabled.
      filter_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
          used in path specification extraction.
      number_of_worker_processes (Optional[int]): number of worker processes.
      status_update_callback (Optional[function]): callback function for status
          updates.
      worker_memory_limit (Optional[int]): maximum amount of memory a worker is
          allowed to consume, where None represents the default memory limit.

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
        logging.error((
            u'Unable to determine number of CPUs defaulting to {0:d} worker '
            u'processes.').format(self._WORKER_PROCESSES_MINIMUM))
        cpu_count = self._WORKER_PROCESSES_MINIMUM

      number_of_worker_processes = cpu_count

    self._enable_sigsegv_handler = enable_sigsegv_handler
    self._number_of_worker_processes = number_of_worker_processes
    self._worker_memory_limit = (
        worker_memory_limit or definitions.DEFAULT_WORKER_MEMORY_LIMIT)

    # Keep track of certain values so we can spawn new extraction workers.
    self._processing_configuration = processing_configuration

    self._filter_find_specs = filter_find_specs
    self._session_identifier = session_identifier
    self._status_update_callback = status_update_callback
    self._storage_writer = storage_writer

    # Set up the task queue.
    if not self._use_zeromq:
      self._task_queue = multi_process_queue.MultiProcessingQueue(
          maximum_number_of_queued_items=self._maximum_number_of_tasks)

    else:
      task_outbound_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
          delay_open=True, linger_seconds=0, maximum_items=1,
          name=u'main_task_queue',
          timeout_seconds=self._ZEROMQ_NO_WORKER_REQUEST_TIME_SECONDS)
      self._task_queue = task_outbound_queue

      # The ZeroMQ backed queue must be started first, so we can save its port.
      # TODO: raises: attribute-defined-outside-init
      # self._task_queue.name = u'Task queue'
      self._task_queue.Open()
      self._task_queue_port = self._task_queue.port

    self._StartProfiling()

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    # Set up the storage writer before the worker processes.
    storage_writer.StartTaskStorage()

    for worker_number in range(number_of_worker_processes):
      # First argument to _StartWorkerProcess is not used.
      extraction_process = self._StartWorkerProcess(u'', storage_writer)
      if not extraction_process:
        logging.error(u'Unable to create worker process: {0:d}'.format(
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

        self._ProcessSources(
            source_path_specs, storage_writer,
            filter_find_specs=filter_find_specs)

      finally:
        storage_writer.WriteSessionCompletion(aborted=self._abort)

        storage_writer.Close()

    finally:
      # Stop the status update thread after close of the storage writer
      # so we include the storage sync to disk in the status updates.
      self._StopStatusUpdateThread()

      if self._serializers_profiler:
        storage_writer.SetSerializersProfiler(None)

      self._StopProfiling()

    try:
      self._StopExtractionProcesses(abort=self._abort)

    except KeyboardInterrupt:
      self._AbortKill()

      # The abort can leave the main process unresponsive
      # due to incorrectly finalized IPC.
      self._KillProcess(os.getpid())

    # The task queue should be closed by _StopExtractionProcesses, this
    # close is a failsafe, primarily due to MultiProcessingQueue's
    # blocking behaviour.
    self._task_queue.Close(abort=True)

    if self._processing_status.error_path_specs:
      task_storage_abort = True
    else:
      task_storage_abort = self._abort

    try:
      storage_writer.StopTaskStorage(abort=task_storage_abort)
    except (IOError, OSError) as exception:
      logging.error(u'Unable to stop task storage with error: {0:s}'.format(
          exception))

    if self._abort:
      logging.debug(u'Processing aborted.')
      self._processing_status.aborted = True
    else:
      logging.debug(u'Processing completed.')

    # Reset values.
    self._enable_sigsegv_handler = None
    self._number_of_worker_processes = None
    self._worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT

    self._processing_configuration = None

    self._filter_find_specs = None
    self._session_identifier = None
    self._status_update_callback = None
    self._storage_writer = None

    return self._processing_status
