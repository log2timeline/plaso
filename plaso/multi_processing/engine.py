# -*- coding: utf-8 -*-
"""The multi-process processing engine."""
import ctypes
import logging
import multiprocessing
import signal
import sys
import threading
import time

from dfvfs.resolver import context

import os
from plaso.containers import event_sources
from plaso.engine import engine, extractors, zeromq_queue, plaso_queue
from plaso.lib import definitions
from plaso.multi_processing import xmlrpc, process_info
from plaso.multi_processing import multi_process
from plaso.multi_processing.worker_process import MultiProcessWorkerProcess


class MultiProcessEngine(engine.BaseEngine):
  """Class that defines the multi-process engine.

  The engine monitors the extraction of events. It monitors:
  * the current file entry a worker is processing;
  * the number of events extracted by each worker;
  * an indicator whether a process is alive or not;
  * the memory consumption of the processes.
  """

  _PROCESS_ABORT_TIMEOUT = 2.0
  _PROCESS_JOIN_TIMEOUT = 5.0
  _PROCESS_TERMINATION_SLEEP = 0.5

  _QUEUE_START_WAIT = 0.3
  _QUEUE_START_WAIT_ATTEMPTS_MAXIMUM = 3

  # Note that on average Windows seems to require a bit longer wait
  # than 5 seconds.
  _RPC_SERVER_TIMEOUT = 8.0
  _MAXIMUM_RPC_ERRORS = 10

  _STATUS_CHECK_SLEEP = 1.5

  _WORKER_PROCESSES_MINIMUM = 2
  _WORKER_PROCESSES_MAXIMUM = 15

  def __init__(self, maximum_number_of_queued_items=0, use_zeromq=False):
    """Initialize the multi-process engine object.

    Args:
      maximum_number_of_queued_items: optional integer containing the maximum
                                      number of queued items. The default is 0,
                                      which represents no limit.
      use_zeromq: optional boolean to indicate whether to use ZeroMQ for
                  queuing. If False, the multiprocessing queue will be used.
    """
    super(MultiProcessEngine, self).__init__()
    self._collector_active = False
    self._collector_thread = None
    self._enable_sigsegv_handler = False
    self._filter_find_specs = None
    self._filter_object = None
    self._hasher_names_string = None
    self._last_worker_number = 0
    self._maximum_number_of_queued_items = maximum_number_of_queued_items
    self._mount_path = None
    self._new_event_sources = False
    self._number_of_consumed_sources = 0
    self._number_of_worker_processes = 0
    self._parser_filter_expression = None
    self._pid = os.getpid()
    self._process_archive_files = False
    self._process_information_per_pid = {}
    self._processes_per_pid = {}
    self._resolver_context = context.Context()
    self._rpc_clients_per_pid = {}
    self._rpc_errors_per_pid = {}
    self._session_identifier = None
    self._show_memory_usage = False
    self._status_update_callback = None
    self._storage_writer = None
    self._tasks = {}
    self._task_queue = None
    self._task_queue_port = None
    self._text_prepend = None
    self._use_zeromq = use_zeromq

  def _AbortJoin(self, timeout=None):
    """Aborts all registered processes by joining with the parent process.

    Args:
      timeout: the process join timeout. The default is None meaning no timeout.
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
    """Check status of a worker process.

    If a worker process is not responding the process is terminated and
    a replacement process is started.

    Args:
      pid (int): process ID (PID) of a registered worker process.

    Raises:
      EngineAbort: when the collector or storage worker process
                   unexpectedly terminates.
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

    if status_indicator == definitions.PROCESSING_STATUS_ERROR:
      path_spec = process_status.get(u'path_spec', None)
      if path_spec:
        self._processing_status.error_path_specs.append(path_spec)

    self._UpdateProcessingStatus(pid, process_status)

    if status_indicator in definitions.PROCESSING_ERROR_STATUS:
      logging.error(
          (u'Process {0:s} (PID: {1:d}) is not functioning correctly. '
           u'Status code {2!s}.').format(
               process.name, pid, status_indicator))

      self._processing_status.error_detected = True

      self._TerminateProcess(pid)

      logging.info(u'Starting replacement worker process for {0:s}'.format(
          process.name))
      worker_process = self._StartExtractionWorkerProcess(self._storage_writer)
      self._StartMonitoringProcess(worker_process.pid)

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

  def _CheckStatusWorkerProcesses(self):
    """Checks status of the worker processes."""
    for pid in iter(self._process_information_per_pid.keys()):
      self._CheckStatusWorkerProcess(pid)

  def _CollectPathSpecs(self):
    """Collects path specifications."""
    logging.debug(u'Collector thread started')

    for event_source in self._storage_writer.GetEventSources():
      self._new_event_sources = True
      if self._abort:
        break

      # TODO: add support for more task types.
      task = multi_process.MultiProcessTask(self._session_identifier)
      task.path_spec = event_source.path_spec

      # TODO: register task with scheduler.
      self._tasks[task.identifier] = task

      self._task_queue.PushItem(task)

    self._collector_active = False
    logging.debug(u'Collector thread stopped.')

  def _GetProcessStatus(self, process):
    """Queries a process to determine its status.

    Args:
      process: The handle to the process to query (instance of
               MultiProcessBaseProcess).

    Returns:
      A dictionary containing the process status.
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
      pid: The process identifier.
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
      pid: The process ID (PID).

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
      source_path_specs: a list of path specifications (instances of
                         dfvfs.PathSpec) of the sources to process.
      storage_writer: a storage writer object (instance of StorageWriter).
      filter_find_specs: optional list of filter find specifications (instances
                         of dfvfs.FindSpec).
    """
    self._number_of_consumed_sources = 0
    number_of_produced_sources = 0

    self._processing_status.UpdateForemanStatus(
        u'Main', definitions.PROCESSING_STATUS_COLLECTING, self._pid, u'',
        self._number_of_consumed_sources, number_of_produced_sources,
        storage_writer.number_of_events, storage_writer.number_of_event_sources)
    self._UpdateStatus()

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

      number_of_produced_sources += 1

      self._processing_status.UpdateForemanStatus(
          u'Main', definitions.PROCESSING_STATUS_COLLECTING, self._pid, u'',
          self._number_of_consumed_sources, number_of_produced_sources,
          storage_writer.number_of_events,
          storage_writer.number_of_event_sources)
      self._UpdateStatus()

    self._new_event_sources = True
    while self._new_event_sources:
      if self._abort:
        return

      # TODO: flushing the storage writer here for now to make sure the event
      # sources are written to disk. Remove this during phased processing
      # refactor.
      storage_writer.ForceFlush()

      self._collector_active = True

      # Set new event sources to false so the collector thread can set
      # it to true when there are new event sources. Since the collector
      # thread is joined before this value is checked again there is
      # no need for a synchronization primitive.
      self._new_event_sources = False
      self._StartCollectorThread()

      # TODO: re-implement abort path on workers idle (raise EngineAbort).
      # TODO: change status check.
      self._CheckStatusWorkerProcesses()

      # TODO: start thread that monitors for new task files.

      while self._collector_active or len(self._tasks):
        self._processing_status.UpdateForemanStatus(
            u'Main', definitions.PROCESSING_STATUS_RUNNING, self._pid, u'',
            self._number_of_consumed_sources, number_of_produced_sources,
            storage_writer.number_of_events,
            storage_writer.number_of_event_sources)
        self._CheckStatusWorkerProcesses()
        self._UpdateStatus()

        # TODO: move task storage merge into separate thread.

        # Make a copy of the keys since we are changing the dictionary
        # inside the loop.
        for task_identifier in list(self._tasks.keys()):
          if self._storage_writer.MergeTaskStorage(task_identifier):
            del self._tasks[task_identifier]

        time.sleep(self._STATUS_CHECK_SLEEP)

      self._StopCollectorThread()

      self._processing_status.UpdateForemanStatus(
          u'Main', definitions.PROCESSING_STATUS_IDLE, self._pid, u'',
          self._number_of_consumed_sources, number_of_produced_sources,
          storage_writer.number_of_events,
          storage_writer.number_of_event_sources)
      self._CheckStatusWorkerProcesses()
      self._UpdateStatus()

    if self._abort:
      status = definitions.PROCESSING_STATUS_ABORTED
    else:
      status = definitions.PROCESSING_STATUS_COMPLETED

    self._processing_status.UpdateForemanStatus(
        u'Main', status, self._pid, u'',
        self._number_of_consumed_sources, number_of_produced_sources,
        storage_writer.number_of_events, storage_writer.number_of_event_sources)
    self._UpdateStatus()

  def _RaiseIfNotMonitored(self, pid):
    """Raises if the process is not monitored by the engine.

    Args:
      pid: The process identifier.

    Raises:
      KeyError: if the process is not monitored by the engine.
    """
    if pid not in self._process_information_per_pid:
      raise KeyError(
          u'Process (PID: {0:d}) not monitored by engine.'.format(pid))

  def _RaiseIfNotRegistered(self, pid):
    """Raises if the process is not registered with the engine.

    Args:
      pid: The process identifier.

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    if pid not in self._processes_per_pid:
      raise KeyError(
          u'Process (PID: {0:d}) not registered with engine'.format(pid))

  def _RegisterProcess(self, process):
    """Registers a process with the engine.

    Args:
      process: The process object (instance of MultiProcessBaseProcess).

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

  def _StartCollectorThread(self):
    """Starts the collector thread."""
    self._collector_thread = threading.Thread(
        name=u'Collector', target=self._CollectPathSpecs)
    self._collector_thread.start()

  def _StartExtractionWorkerProcess(self, storage_writer):
    """Creates, starts and registers an extraction worker process.

    Args:
      storage_writer: a storage writer object (instance of StorageWriter).

    Returns:
      An extraction worker process (instance of MultiProcessWorkerProcess).
    """
    process_name = u'Worker_{0:02d}'.format(self._last_worker_number)

    if self._use_zeromq:
      task_queue = zeromq_queue.ZeroMQRequestConnectQueue(
          delay_open=True, name=u'{0:s} pathspec'.format(process_name),
          linger_seconds=0, port=self._task_queue_port,
          timeout_seconds=2)
    else:
      task_queue = self._task_queue

    worker_process = MultiProcessWorkerProcess(
        task_queue, storage_writer, self.knowledge_base,
        self._session_identifier, self._last_worker_number,
        enable_debug_output=self._enable_debug_output,
        enable_profiling=self._enable_profiling,
        enable_sigsegv_handler=self._enable_sigsegv_handler,
        filter_object=self._filter_object,
        hasher_names_string=self._hasher_names_string,
        mount_path=self._mount_path, name=process_name,
        parser_filter_expression=self._parser_filter_expression,
        process_archive_files=self._process_archive_files,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type, text_prepend=self._text_prepend)

    worker_process.start()
    self._last_worker_number += 1

    self._RegisterProcess(worker_process)

    return worker_process

  def _StartMonitoringProcess(self, pid):
    """Starts monitoring a process.

    Args:
      pid: The process identifier.

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

  def _StopCollectorThread(self):
    """Stops the collector thread."""
    if self._collector_thread.isAlive():
      self._collector_thread.join()
    self._collector_thread = None

  def _StopExtractionProcesses(self, abort=False):
    """Stops the extraction processes.

    Args:
      abort: optional boolean to indicate the stop is issued on abort.
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
    if isinstance(self._task_queue, multi_process.MultiProcessingQueue):
      self._task_queue.Close(abort=True)

    if abort:
      # Kill any remaining processes, which can be necessary if
      # the collector dies.
      self._AbortKill()

  def _StopMonitoringProcess(self, pid):
    """Stops monitoring a process.

    Args:
      pid: The process identifier.

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

  def _TerminateProcess(self, pid):
    """Terminate a process.

    Args:
      pid: The process identifier.

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
      process_status (dict): status values received from the worker process.

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    self._RaiseIfNotRegistered(pid)

    if not process_status:
      return

    process = self._processes_per_pid[pid]

    processing_status = process_status.get(u'processing_status', None)

    self._RaiseIfNotMonitored(pid)

    number_of_consumed_events = process_status.get(
        u'number_of_consumed_events', 0)
    number_of_consumed_sources = process_status.get(
        u'number_of_consumed_sources', 0)
    display_name = process_status.get(u'display_name', u'')
    number_of_produced_events = process_status.get(
        u'number_of_produced_events', 0)
    number_of_produced_sources = process_status.get(
        u'number_of_produced_sources', 0)

    self._processing_status.UpdateWorkerStatus(
        process.name, processing_status, pid, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events)

  def _UpdateStatus(self):
    """Updates the processing status."""
    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

  def ProcessSources(
      self, source_path_specs, session_start, preprocess_object,
      storage_writer, enable_sigsegv_handler=False, filter_find_specs=None,
      filter_object=None, hasher_names_string=None, mount_path=None,
      number_of_worker_processes=0, parser_filter_expression=None,
      process_archive_files=False, profiling_type=u'all',
      status_update_callback=None, show_memory_usage=False, text_prepend=None):
    """Processes the sources and extract event objects.

    Args:
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      session_start: a session start attribute container (instance of
                     SessionStart).
      preprocess_object: a preprocess object (instance of PreprocessObject).
      storage_writer: a storage writer object (instance of StorageWriter).
      enable_sigsegv_handler: optional boolean value to indicate the SIGSEGV
                              handler should be enabled.
      filter_find_specs: optional list of filter find specifications (instances
                         of dfvfs.FindSpec).
      filter_object: optional filter object (instance of objectfilter.Filter).
      hasher_names_string: optional comma separated string of names of
                           hashers to enable enable.
      mount_path: optional string containing the mount path.
      number_of_worker_processes: optional integer containing the number of
                                  worker processes. The default is 0 which
                                  means the function will determine the
                                  suitable number.
      parser_filter_expression: optional string containing the parser filter
                                expression, where None represents all parsers
                                and plugins.
      process_archive_files: optional boolean value to indicate if the worker
                             should scan for file entries inside files.
      profiling_type: optional string containing the profiling type.
      status_update_callback: optional callback function for status updates.
      show_memory_usage: optional boolean value to indicate memory information
                         should be included in logging.
      text_prepend: optional string that contains the text to prepend to every
                    event object.

    Returns:
      The processing status (instance of ProcessingStatus).
    """
    if number_of_worker_processes < 1:
      # One worker for each "available" CPU (minus other processes).
      # The number here is derived from the fact that the engine starts up:
      # * A collector process.
      # * A storage process.
      #
      # If we want to utilize all CPUs on the system we therefore need to start
      # up workers that amounts to the total number of CPUs - the other
      # processes.
      cpu_count = multiprocessing.cpu_count() - 2

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
    self._process_archive_files = process_archive_files
    self._session_identifier = session_start.identifier
    self._status_update_callback = status_update_callback
    self._storage_writer = storage_writer
    self._text_prepend = text_prepend

    # Set up the storage writer before the worker processes.
    self._storage_writer.StartTaskStorage()

    # Set up the task queue.
    if not self._use_zeromq:
      self._task_queue = multi_process.MultiProcessingQueue(
          maximum_number_of_queued_items=self._maximum_number_of_queued_items)

    else:
      task_outbound_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
          delay_open=True, name=u'Task queue', buffer_timeout_seconds=300)
      self._task_queue = task_outbound_queue

      # The ZeroMQ backed queue must be started first, so we can save its port.
      # TODO: raises: attribute-defined-outside-init
      # self._task_queue.name = u'Task queue'
      self._task_queue.Open()
      self._task_queue_port = self._task_queue.port

    # Start the worker processes.
    logging.debug(u'Starting processes.')

    for _ in range(0, number_of_worker_processes):
      extraction_process = self._StartExtractionWorkerProcess(
          self._storage_writer)
      self._StartMonitoringProcess(extraction_process.pid)

    logging.debug(u'Processing started.')

    self._storage_writer.Open()

    if self._enable_profiling:
      self._storage_writer.EnableProfiling(profiling_type=profiling_type)

    self._storage_writer.WriteSessionStart(session_start)

    # TODO: change in phased processing refactor.
    self._ProcessSources(
        source_path_specs, self._storage_writer,
        filter_find_specs=filter_find_specs)

    if self._abort:
      return

    self._StopExtractionProcesses(abort=self._processing_status.error_detected)

    logging.debug(u'Processing stopped.')

    # TODO: refactor the use of preprocess_object.
    self._storage_writer.WritePreprocessObject(preprocess_object)
    self._storage_writer.WriteSessionCompletion()
    self._storage_writer.Close()

    if self._enable_profiling:
      self._storage_writer.DisableProfiling()

    self._storage_writer.StopTaskStorage()

    self._task_queue.Close(abort=self._abort)

    # Reset values.
    self._enable_sigsegv_handler = None
    self._number_of_worker_processes = None
    self._show_memory_usage = None

    self._filter_find_specs = None
    self._filter_object = None
    self._hasher_names_string = None
    self._mount_path = None
    self._parser_filter_expression = None
    self._process_archive_files = None
    self._session_identifier = None
    self._status_update_callback = None
    self._storage_writer = None
    self._text_prepend = None

    return self._processing_status

  def SignalAbort(self):
    """Signals the engine to abort."""
    try:
      self._StopExtractionProcesses(abort=True)

    except KeyboardInterrupt:
      self._AbortKill()

      # The abort can leave the main process unresponsive
      # due to incorrectly finalized IPC.
      self._KillProcess(os.getpid())
