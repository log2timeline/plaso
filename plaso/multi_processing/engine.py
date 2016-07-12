# -*- coding: utf-8 -*-
"""The multi-process processing engine."""

import ctypes
import logging
import multiprocessing
import os
import Queue
import signal
import sys
import threading
import time

from dfvfs.resolver import context

from plaso.containers import event_sources
from plaso.engine import engine
from plaso.engine import extractors
from plaso.engine import plaso_queue
from plaso.engine import profiler
from plaso.engine import zeromq_queue
from plaso.lib import definitions
from plaso.multi_processing import multi_process_queue
from plaso.multi_processing import process_info
from plaso.multi_processing import task_manager
from plaso.multi_processing import worker_process
from plaso.multi_processing import xmlrpc


class MultiProcessEngine(engine.BaseEngine):
  """Class that defines the multi-process engine.

  The engine monitors the extraction of events. It monitors:
  * the current file entry a worker is processing;
  * the number of events extracted by each worker;
  * an indicator whether a process is alive or not;
  * the memory consumption of the processes.
  """

  # Maximum number of concurrent tasks.
  _MAXIMUM_NUMBER_OF_TASKS = 10000

  _PROCESS_ABORT_TIMEOUT = 2.0
  _PROCESS_JOIN_TIMEOUT = 5.0
  _PROCESS_TERMINATION_SLEEP = 0.5

  _QUEUE_START_WAIT = 0.3
  _QUEUE_START_WAIT_ATTEMPTS_MAXIMUM = 3

  # Note that on average Windows seems to require a bit longer wait
  # than 5 seconds.
  _RPC_SERVER_TIMEOUT = 8.0
  _MAXIMUM_RPC_ERRORS = 10

  _WORKER_PROCESSES_MINIMUM = 2
  _WORKER_PROCESSES_MAXIMUM = 15

  def __init__(
      self, enable_profiling=False,
      maximum_number_of_tasks=_MAXIMUM_NUMBER_OF_TASKS,
      profiling_directory=None, profiling_sample_rate=1000,
      profiling_type=u'all', use_zeromq=True):
    """Initializes an engine object.

    Args:
      enable_profiling (Optional[bool]): True if profiling should be enabled.
      maximum_number_of_tasks (Optional[int]): maximum number of concurrent
          tasks, where 0 represents no limit.
      profiling_directory (Optional[str]): path to the directory where
          the profiling sample files should be stored.
      profiling_sample_rate (Optional[int]): the profiling sample rate.
          Contains the number of event sources processed.
      profiling_type (Optional[str]): type of profiling.
          Supported types are:

          * 'memory' to profile memory usage;
          * 'parsers' to profile CPU time consumed by individual parsers;
          * 'processing' to profile CPU time consumed by different parts of
            the processing;
          * 'serializers' to profile CPU time consumed by individual
            serializers.
      use_zeromq (Optional[bool]): True if ZeroMQ should be used for queuing
          instead of Python's multiprocessing queue.
    """
    super(MultiProcessEngine, self).__init__(
        enable_profiling=enable_profiling,
        profiling_directory=profiling_directory,
        profiling_sample_rate=profiling_sample_rate,
        profiling_type=profiling_type)
    self._enable_sigsegv_handler = False
    self._filter_find_specs = None
    self._filter_object = None
    self._hasher_names_string = None
    self._last_status_update_timestamp = 0.0
    self._last_worker_number = 0
    self._maximum_number_of_tasks = maximum_number_of_tasks
    self._memory_profiler = None
    self._merge_task_identifier = u''
    self._mount_path = None
    self._name = u'Main'
    self._number_of_consumed_errors = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_errors = 0
    self._number_of_produced_events = 0
    self._number_of_produced_sources = 0
    self._number_of_worker_processes = 0
    self._parser_filter_expression = None
    self._pid = os.getpid()
    self._preferred_year = None
    self._process_archive_files = False
    self._processes_per_pid = {}
    self._process_information_per_pid = {}
    self._processing_profiler = None
    self._resolver_context = context.Context()
    self._rpc_clients_per_pid = {}
    self._rpc_errors_per_pid = {}
    self._serializers_profiler = None
    self._session_identifier = None
    self._show_memory_usage = False
    self._status = definitions.PROCESSING_STATUS_IDLE
    self._status_update_active = False
    self._status_update_callback = None
    self._status_update_thread = None
    self._storage_writer = None
    self._task_queue = None
    self._task_queue_port = None
    self._task_manager = task_manager.TaskManager(
        maximum_number_of_tasks=maximum_number_of_tasks)
    self._task_scheduler_active = False
    self._task_scheduler_thread = None
    self._temporary_directory = None
    self._text_prepend = None
    self._use_zeromq = use_zeromq

  def _AbortJoin(self, timeout=None):
    """Aborts all registered processes by joining with the parent process.

    Args:
      timeout (int): the process join timeout, where None represents no timeout.
    """
    for pid, process in iter(self._processes_per_pid.items()):
      logging.debug(u'Waiting for process: {0:s} (PID: {1:d}).'.format(
          process.name, pid))
      process.join(timeout=timeout)
      if not process.is_alive():
        logging.debug(u'Process {0:s} (PID: {1:d}) stopped.'.format(
            process.name, pid))

  def _AbortKill(self):
    """Aborts all registered processes by sending a SIGKILL or equivalent."""
    for pid, process in iter(self._processes_per_pid.items()):
      if not process.is_alive():
        continue

      logging.warning(u'Killing process: {0:s} (PID: {1:d}).'.format(
          process.name, pid))
      self._KillProcess(pid)

  def _AbortTerminate(self):
    """Aborts all registered processes by sending a SIGTERM or equivalent."""
    for pid, process in iter(self._processes_per_pid.items()):
      if not process.is_alive():
        continue

      logging.warning(u'Terminating process: {0:s} (PID: {1:d}).'.format(
          process.name, pid))
      process.terminate()

  def _CheckStatusWorkerProcess(self, pid):
    """Checks the status of a worker process.

    If a worker process is not responding the process is terminated and
    a replacement process is started.

    Args:
      pid (int): process ID (PID) of a registered worker process.

    Raises:
      EngineAbort: when the worker process unexpectedly terminates.
      KeyError: if the process is not registered with the engine.
    """
    # TODO: Refactor this method, simplify and separate concerns (monitoring
    # vs management).
    self._RaiseIfNotRegistered(pid)

    process = self._processes_per_pid[pid]

    process_status = self._GetProcessStatus(process)
    if process_status is None:
      process_is_alive = False
    else:
      process_is_alive = True

    if isinstance(process_status, dict):
      self._rpc_errors_per_pid[pid] = 0
      status_indicator = process_status.get(u'processing_status', None)

    else:
      rpc_errors = self._rpc_errors_per_pid.get(pid, 0) + 1
      self._rpc_errors_per_pid[pid] = rpc_errors

      if rpc_errors > self._MAXIMUM_RPC_ERRORS:
        process_is_alive = False

      if process_is_alive:
        rpc_port = process.rpc_port.value
        logging.warning((
            u'Unable to retrieve process: {0:s} (PID: {1:d}) status via '
            u'RPC socket: http://localhost:{2:d}').format(
                process.name, pid, rpc_port))

        processing_status_string = u'RPC error'
        status_indicator = definitions.PROCESSING_STATUS_RUNNING
      else:
        processing_status_string = u'killed'
        status_indicator = definitions.PROCESSING_STATUS_KILLED

      process_status = {
          u'processing_status': processing_status_string,
      }

    self._UpdateProcessingStatus(pid, process_status)

    if status_indicator in definitions.PROCESSING_ERROR_STATUS:
      logging.error(
          (u'Process {0:s} (PID: {1:d}) is not functioning correctly. '
           u'Status code: {2!s}.').format(
               process.name, pid, status_indicator))

      self._TerminateProcess(pid)

      logging.info(u'Starting replacement worker process for {0:s}'.format(
          process.name))
      replacement_process = self._StartExtractionWorkerProcess(
          self._storage_writer)
      self._StartMonitoringProcess(replacement_process.pid)

    elif status_indicator == definitions.PROCESSING_STATUS_COMPLETED:
      number_of_events = process_status.get(u'number_of_events', 0)
      number_of_sources = process_status.get(u'number_of_consumed_sources', 0)
      logging.debug((
          u'Process {0:s} (PID: {1:d}) has completed its processing. '
          u'Total of {2:d} events extracted from {3:d} sources').format(
              process.name, pid, number_of_events, number_of_sources))

      self._StopMonitoringProcess(pid)

    elif self._show_memory_usage:
      self._LogMemoryUsage(pid)

  def _GetProcessStatus(self, process):
    """Queries a process to determine its status.

    Args:
      process (MultiProcessBaseProcess): process to query for its status.

    Returns:
      dict[str, str]: status values received from the worker process.
    """
    process_is_alive = process.is_alive()
    if process_is_alive:
      rpc_client = self._rpc_clients_per_pid.get(process.pid, None)
      process_status = rpc_client.CallFunction()
    else:
      process_status = None
    return process_status

  def _KillProcess(self, pid):
    """Issues a SIGKILL or equivalent to the process.

    Args:
      pid (int): process identifier (PID).
    """
    if sys.platform.startswith(u'win'):
      process_terminate = 1
      handle = ctypes.windll.kernel32.OpenProcess(
          process_terminate, False, pid)
      ctypes.windll.kernel32.TerminateProcess(handle, -1)
      ctypes.windll.kernel32.CloseHandle(handle)

    else:
      try:
        os.kill(pid, signal.SIGKILL)
      except OSError as exception:
        logging.error(u'Unable to kill process {0:d} with error: {1:s}'.format(
            pid, exception))

  def _LogMemoryUsage(self, pid):
    """Logs memory information gathered from a process.

    Args:
      pid (int): process identifier (PID).

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    self._RaiseIfNotRegistered(pid)
    self._RaiseIfNotMonitored(pid)

    process = self._processes_per_pid[pid]
    process_information = self._process_information_per_pid[pid]
    memory_info = process_information.GetMemoryInformation()
    logging.debug((
        u'{0:s} - RSS: {1:d}, VMS: {2:d}, Shared: {3:d}, Text: {4:d}, lib: '
        u'{5:d}, data: {6:d}, dirty: {7:d}, Memory Percent: {8:0.2f}%').format(
            process.name, memory_info.rss, memory_info.vms,
            memory_info.shared, memory_info.text, memory_info.lib,
            memory_info.data, memory_info.dirty, memory_info.percent * 100))

  def _ProcessSources(
      self, source_path_specs, storage_writer, filter_find_specs=None):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      storage_writer (StorageWriter): storage writer for a session storage.
      filter_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
          used in path specification extraction.
    """
    self._status = definitions.PROCESSING_STATUS_COLLECTING
    self._number_of_consumed_errors = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_errors = 0
    self._number_of_produced_events = 0
    self._number_of_produced_sources = 0

    path_spec_extractor = extractors.PathSpecExtractor(self._resolver_context)

    for path_spec in path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=filter_find_specs,
        recurse_file_system=False):
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

  def _ProfilingSampleMemory(self):
    """Creates a memory profiling sample."""
    if self._memory_profiler:
      self._memory_profiler.Sample()

  def _RaiseIfNotMonitored(self, pid):
    """Raises if the process is not monitored by the engine.

    Args:
      pid (int): process identifier (PID).

    Raises:
      KeyError: if the process is not monitored by the engine.
    """
    if pid not in self._process_information_per_pid:
      raise KeyError(
          u'Process (PID: {0:d}) not monitored by engine.'.format(pid))

  def _RaiseIfNotRegistered(self, pid):
    """Raises if the process is not registered with the engine.

    Args:
      pid (int): process identifier (PID).

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    if pid not in self._processes_per_pid:
      raise KeyError(
          u'Process (PID: {0:d}) not registered with engine'.format(pid))

  def _RegisterProcess(self, process):
    """Registers a process with the engine.

    Args:
      process (MultiProcessBaseProcess): process.

    Raises:
      KeyError: if the process is already registered with the engine.
      ValueError: if the process object is missing.
    """
    if process is None:
      raise ValueError(u'Missing process object.')

    if process.pid in self._processes_per_pid:
      raise KeyError(
          u'Already managing process: {0!s} (PID: {1:d})'.format(
              process.name, process.pid))

    self._processes_per_pid[process.pid] = process

  def _ScheduleTasks(self, storage_writer):
    """Schedule tasks.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage used
          to merge task storage.
    """
    logging.debug(u'Task scheduler started')

    self._status = definitions.PROCESSING_STATUS_RUNNING

    # TODO: make tasks persistent.

    # TODO: protect task scheduler loop by catch all and
    # handle abort path.

    task = None

    new_event_sources = True
    while new_event_sources:
      if self._abort:
        return

      new_event_sources = False
      event_source = storage_writer.GetNextEventSource()
      while event_source or self._task_manager.HasScheduledTasks():
        new_event_sources = True
        if self._abort:
          break

        if event_source and not task:
          task = self._task_manager.CreateTask(self._session_identifier)
          task.path_spec = event_source.path_spec
          event_source = None

          self._number_of_consumed_sources += 1

          if self._memory_profiler:
            self._memory_profiler.Sample()

        if task:
          try:
            self._task_queue.PushItem(task, block=False)
            self._task_manager.ScheduleTask(task.identifier)
            task = None

          except Queue.Full:
            pass

        # GetScheduledTaskIdentifiers makes a copy of the keys since we are
        # changing the dictionary inside the loop.
        task_storage_merged = False
        for task_identifier in self._task_manager.GetScheduledTaskIdentifiers():
          if self._abort:
            break

          if storage_writer.CheckTaskStorageReadyForMerge(
              task_identifier):
            # Make sure completed tasks are not considered idle when not
            # yet merged.
            self._task_manager.UpdateTask(task_identifier)

          # Merge one task-based storage file per loop to keep tasks flowing.
          if task_storage_merged:
            continue

          self._status = definitions.PROCESSING_STATUS_MERGING
          self._merge_task_identifier = task_identifier

          if self._processing_profiler:
            self._processing_profiler.StartTiming(u'merge')

          # TODO: look into time slicing merge.
          if storage_writer.MergeTaskStorage(task_identifier):
            self._task_manager.CompleteTask(task_identifier)
            task_storage_merged = True

          if self._processing_profiler:
            self._processing_profiler.StopTiming(u'merge')

          self._status = definitions.PROCESSING_STATUS_RUNNING
          self._merge_task_identifier = u''
          self._number_of_produced_errors = storage_writer.number_of_errors
          self._number_of_produced_events = storage_writer.number_of_events
          self._number_of_produced_sources = (
              storage_writer.number_of_event_sources)

        if not event_source and not task:
          event_source = storage_writer.GetNextEventSource()

      for task in self._task_manager.GetAbandonedTasks():
        self._processing_status.error_path_specs.append(task.path_spec)

    self._status = definitions.PROCESSING_STATUS_IDLE

    if self._abort:
      logging.debug(u'Task scheduler aborted')
    else:
      logging.debug(u'Task scheduler stopped')

  def _StartExtractionWorkerProcess(self, storage_writer):
    """Creates, starts and registers an extraction worker process.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage used
          to create task storage.

    Returns:
      MultiProcessWorkerProcess: extraction worker process.
    """
    process_name = u'Worker_{0:02d}'.format(self._last_worker_number)

    if self._use_zeromq:
      task_queue = zeromq_queue.ZeroMQRequestConnectQueue(
          delay_open=True, name=u'{0:s} pathspec'.format(process_name),
          linger_seconds=0, port=self._task_queue_port,
          timeout_seconds=2)
    else:
      task_queue = self._task_queue

    process = worker_process.WorkerProcess(
        task_queue, storage_writer, self.knowledge_base,
        self._session_identifier, self._last_worker_number,
        enable_debug_output=self._enable_debug_output,
        enable_profiling=self._enable_profiling,
        enable_sigsegv_handler=self._enable_sigsegv_handler,
        filter_object=self._filter_object,
        hasher_names_string=self._hasher_names_string,
        mount_path=self._mount_path, name=process_name,
        parser_filter_expression=self._parser_filter_expression,
        preferred_year=self._preferred_year,
        process_archive_files=self._process_archive_files,
        profiling_directory=self._profiling_directory,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type,
        temporary_directory=self._temporary_directory,
        text_prepend=self._text_prepend)

    process.start()
    self._last_worker_number += 1

    self._RegisterProcess(process)

    return process

  def _StartMonitoringProcess(self, pid):
    """Starts monitoring a process.

    Args:
      pid (int): process identifier (PID).

    Raises:
      KeyError: if the process is not registered with the engine or
                if the process if the processed is already being monitored.
      IOError: if the RPC client cannot connect to the server.
    """
    self._RaiseIfNotRegistered(pid)

    if pid in self._process_information_per_pid:
      raise KeyError(
          u'Process (PID: {0:d}) already in monitoring list.'.format(pid))

    if pid in self._rpc_clients_per_pid:
      raise KeyError(
          u'RPC client (PID: {0:d}) already exists'.format(pid))

    process = self._processes_per_pid[pid]
    rpc_client = xmlrpc.XMLProcessStatusRPCClient()

    # Make sure that a process has started its RPC server. RPC port will
    # be 0 if no server is available.
    rpc_port = process.rpc_port.value
    time_waited_for_process = 0.0
    while not rpc_port:
      time.sleep(0.1)
      rpc_port = process.rpc_port.value
      time_waited_for_process += 0.1

      if time_waited_for_process >= self._RPC_SERVER_TIMEOUT:
        raise IOError(
            u'RPC client unable to determine server (PID: {0:d}) port.'.format(
                pid))

    hostname = u'localhost'

    if not rpc_client.Open(hostname, rpc_port):
      raise IOError((
          u'RPC client unable to connect to server (PID: {0:d}) '
          u'http://{1:s}:{2:d}').format(pid, hostname, rpc_port))

    self._rpc_clients_per_pid[pid] = rpc_client
    self._process_information_per_pid[pid] = process_info.ProcessInfo(pid)

  def _StartProfiling(self):
    """Starts profiling."""
    if not self._enable_profiling:
      return

    if self._profiling_type in (u'all', u'memory'):
      identifier = u'{0:s}-memory'.format(self._name)
      self._memory_profiler = profiler.GuppyMemoryProfiler(
          identifier, path=self._profiling_directory,
          profiling_sample_rate=self._profiling_sample_rate)
      self._memory_profiler.Start()

    if self._profiling_type in (u'all', u'processing'):
      identifier = u'{0:s}-processing'.format(self._name)
      self._processing_profiler = profiler.ProcessingProfiler(
          identifier, path=self._profiling_directory)

    if self._profiling_type in (u'all', u'serializers'):
      identifier = u'{0:s}-serializers'.format(self._name)
      self._serializers_profiler = profiler.SerializersProfiler(
          identifier, path=self._profiling_directory)

  def _StartStatusUpdateThread(self):
    """Starts the status update thread."""
    self._status_update_active = True
    self._status_update_thread = threading.Thread(
        name=u'Status update', target=self._StatusUpdateThreadMain)
    self._status_update_thread.start()

  def _StatusUpdateThreadMain(self):
    """Main function of the status update thread."""
    while self._status_update_active:
      # Make a local copy of the PIDs in case the dict changes by
      # the main thread.
      for pid in list(self._process_information_per_pid.keys()):
        self._CheckStatusWorkerProcess(pid)

      self._processing_status.UpdateForemanStatus(
          self._name, self._status, self._pid, self._merge_task_identifier,
          self._number_of_consumed_sources, self._number_of_produced_sources,
          self._number_of_consumed_events, self._number_of_produced_events,
          self._number_of_consumed_errors, self._number_of_produced_errors)

      if self._status_update_callback:
        self._status_update_callback(self._processing_status)

      time.sleep(self._STATUS_UPDATE_INTERVAL)

  def _StopExtractionProcesses(self, abort=False):
    """Stops the extraction processes.

    Args:
      abort (bool): True to indicated the stop is issued on abort.
    """
    logging.debug(u'Stopping extraction processes.')
    self._StopProcessMonitoring()

    # Note that multiprocessing.Queue is very sensitive regarding
    # blocking on either a get or a put. So we try to prevent using
    # any blocking behavior.

    if abort:
      # Signal all the processes to abort.
      self._AbortTerminate()

    # Wake the processes to make sure that they are not blocking
    # waiting for the queue not to be full.
    if not self._use_zeromq:
      logging.debug(u'Emptying queues.')
      self._task_queue.Empty()

      # Wake the processes to make sure that they are not blocking
      # waiting for new items.
      for _ in range(self._number_of_worker_processes):
        self._task_queue.PushItem(plaso_queue.QueueAbort(), block=False)

    # Try waiting for the processes to exit normally.
    self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)

    if not abort:
      # Check if the processes are still alive and terminate them if necessary.
      self._AbortTerminate()
      self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)

    # For Multiprocessing queues, set abort to True to stop queue.join_thread()
    # from blocking.
    if isinstance(self._task_queue, multi_process_queue.MultiProcessingQueue):
      self._task_queue.Close(abort=True)

    if abort:
      # Kill any remaining processes.
      self._AbortKill()

  def _StopMonitoringProcess(self, pid):
    """Stops monitoring a process.

    Args:
      pid (int): process identifier (PID).

    Raises:
      KeyError: if the process is not registered with the engine or
                if the process is registered, but not monitored.
    """
    self._RaiseIfNotRegistered(pid)
    self._RaiseIfNotMonitored(pid)

    process = self._processes_per_pid[pid]
    del self._process_information_per_pid[pid]

    rpc_client = self._rpc_clients_per_pid.get(pid, None)
    if rpc_client:
      rpc_client.Close()
      del self._rpc_clients_per_pid[pid]

    if pid in self._rpc_errors_per_pid:
      del self._rpc_errors_per_pid[pid]

    logging.debug((
        u'Process: {0:s} (PID: {1:d}) has been removed from the monitoring '
        u'list.').format(process.name, pid))

  def _StopProcessMonitoring(self):
    """Stops monitoring processes."""
    for pid in iter(self._process_information_per_pid.keys()):
      self._StopMonitoringProcess(pid)

  def _StopProfiling(self):
    """Stops profiling."""
    if not self._enable_profiling:
      return

    if self._profiling_type in (u'all', u'memory'):
      self._memory_profiler.Sample()
      self._memory_profiler = None

    if self._profiling_type in (u'all', u'processing'):
      self._processing_profiler.Write()
      self._processing_profiler = None

    if self._profiling_type in (u'all', u'serializers'):
      self._serializers_profiler.Write()
      self._serializers_profiler = None

  def _StopStatusUpdateThread(self):
    """Stops the status update thread."""
    self._status_update_active = False
    if self._status_update_thread.isAlive():
      self._status_update_thread.join()
    self._status_update_thread = None

  def _TerminateProcess(self, pid):
    """Terminate a process.

    Args:
      pid (int): process identifier (PID).

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    self._RaiseIfNotRegistered(pid)

    process = self._processes_per_pid[pid]

    logging.warning(u'Terminating process: (PID: {0:d}).'.format(pid))
    process.terminate()

    if process.is_alive():
      logging.warning(u'Killing process: (PID: {0:d}).'.format(pid))
      self._KillProcess(pid)

    self._StopMonitoringProcess(pid)

  def _UpdateProcessingStatus(self, pid, process_status):
    """Updates the processing status.

    Args:
      pid (int): process identifier (PID) of the worker process.
      process_status (dict[str, str]): status values received from
          the worker process.

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
        u'number_of_consumed_errors', 0)
    number_of_produced_errors = process_status.get(
        u'number_of_produced_errors', 0)
    number_of_consumed_events = process_status.get(
        u'number_of_consumed_events', 0)
    number_of_produced_events = process_status.get(
        u'number_of_produced_events', 0)
    number_of_consumed_sources = process_status.get(
        u'number_of_consumed_sources', 0)
    number_of_produced_sources = process_status.get(
        u'number_of_produced_sources', 0)

    self._processing_status.UpdateWorkerStatus(
        process.name, processing_status, pid, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events,
        number_of_consumed_errors, number_of_produced_errors)

    task_identifier = process_status.get(u'task_identifier', u'')
    if task_identifier:
      try:
        self._task_manager.UpdateTask(task_identifier)
      except KeyError:
        logging.error(u'Worker processing untracked task.')

  def ProcessSources(
      self, session_identifier, source_path_specs, preprocess_object,
      storage_writer, enable_sigsegv_handler=False, filter_find_specs=None,
      filter_object=None, hasher_names_string=None, mount_path=None,
      number_of_worker_processes=0, parser_filter_expression=None,
      preferred_year=None, process_archive_files=False,
      status_update_callback=None, show_memory_usage=False,
      temporary_directory=None, text_prepend=None):
    """Processes the sources and extract event objects.

    Args:
      session_identifier (str): identifier of the session.
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      preprocess_object (PreprocessObject): preprocess object.
      storage_writer (StorageWriter): storage writer for a session storage.
      enable_sigsegv_handler (Optional[bool]): True if the SIGSEGV handler
          should be enabled.
      filter_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
          used in path specification extraction.
      filter_object (Optional[objectfilter.Filter]): filter object.
      hasher_names_string (Optional[str]): comma separated string of names
          of hashers to use during processing.
      mount_path (Optional[str]): mount path.
      number_of_worker_processes (Optional[int]): number of worker processes.
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.
      preferred_year (Optional[int]): preferred year.
      process_archive_files (Optional[bool]): True if archive files should be
          scanned for file entries.
      show_memory_usage (Optional[bool]): True if memory information should be
          included in status updates.
      status_update_callback (Optional[function]): callback function for status
          updates.
      temporary_directory (Optional[str]): path of the directory for temporary
          files.
      text_prepend (Optional[str]): text to prepend to every event.

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
      cpu_count = multiprocessing.cpu_count() - 1

      if cpu_count <= self._WORKER_PROCESSES_MINIMUM:
        cpu_count = self._WORKER_PROCESSES_MINIMUM

      elif cpu_count >= self._WORKER_PROCESSES_MAXIMUM:
        cpu_count = self._WORKER_PROCESSES_MAXIMUM

      number_of_worker_processes = cpu_count

    self._enable_sigsegv_handler = enable_sigsegv_handler
    self._number_of_worker_processes = number_of_worker_processes
    self._show_memory_usage = show_memory_usage

    # Keep track of certain values so we can spawn new extraction workers.
    self._filter_find_specs = filter_find_specs
    self._filter_object = filter_object
    self._hasher_names_string = hasher_names_string
    self._mount_path = mount_path
    self._parser_filter_expression = parser_filter_expression
    self._preferred_year = preferred_year
    self._process_archive_files = process_archive_files
    self._session_identifier = session_identifier
    self._status_update_callback = status_update_callback
    self._storage_writer = storage_writer
    self._temporary_directory = temporary_directory
    self._text_prepend = text_prepend

    # Set up the storage writer before the worker processes.
    storage_writer.StartTaskStorage()

    # Set up the task queue.
    if not self._use_zeromq:
      self._task_queue = multi_process_queue.MultiProcessingQueue(
          maximum_number_of_queued_items=self._maximum_number_of_tasks)

    else:
      task_outbound_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
          delay_open=True, name=u'Task queue', buffer_timeout_seconds=300)
      self._task_queue = task_outbound_queue

      # The ZeroMQ backed queue must be started first, so we can save its port.
      # TODO: raises: attribute-defined-outside-init
      # self._task_queue.name = u'Task queue'
      self._task_queue.Open()
      self._task_queue_port = self._task_queue.port

    for _ in range(0, number_of_worker_processes):
      extraction_process = self._StartExtractionWorkerProcess(storage_writer)
      self._StartMonitoringProcess(extraction_process.pid)

    self._StartProfiling()

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    storage_writer.Open()

    # Start the status update thread after open of the storage writer
    # so we don't have to clean up the thread if the open fails.
    self._StartStatusUpdateThread()

    try:
      storage_writer.WriteSessionStart()

      self._ProcessSources(
          source_path_specs, storage_writer,
          filter_find_specs=filter_find_specs)

      # TODO: refactor the use of preprocess_object.
      storage_writer.WritePreprocessObject(preprocess_object)

      # TODO: on abort use WriteSessionAborted instead of completion?
      storage_writer.WriteSessionCompletion()

    finally:
      storage_writer.Close()

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

    self._task_queue.Close(abort=self._abort)

    if self._processing_status.error_path_specs:
      task_storage_abort = True
    else:
      task_storage_abort = self._abort

    storage_writer.StopTaskStorage(abort=task_storage_abort)

    if self._abort:
      logging.debug(u'Processing aborted.')
      self._processing_status.aborted = True
    else:
      logging.debug(u'Processing completed.')

    # Reset values.
    self._enable_sigsegv_handler = None
    self._number_of_worker_processes = None
    self._show_memory_usage = None

    self._filter_find_specs = None
    self._filter_object = None
    self._hasher_names_string = None
    self._mount_path = None
    self._parser_filter_expression = None
    self._preferred_year = None
    self._process_archive_files = None
    self._session_identifier = None
    self._status_update_callback = None
    self._storage_writer = None
    self._text_prepend = None

    return self._processing_status
