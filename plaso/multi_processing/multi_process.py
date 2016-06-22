# -*- coding: utf-8 -*-
"""The multi-process processing engine."""

import abc
import ctypes
import glob
import logging
import multiprocessing
import os
import Queue
import random
import signal
import sys
import threading
import time
import uuid

from dfvfs.resolver import context

from plaso.containers import event_sources
from plaso.containers import tasks
from plaso.engine import engine
from plaso.engine import extractors
from plaso.engine import plaso_queue
from plaso.engine import worker
from plaso.engine import zeromq_queue
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import process_info
from plaso.multi_processing import xmlrpc
from plaso.parsers import mediator as parsers_mediator
from plaso.storage import zip_file as storage_zip_file


class MultiProcessTask(multiprocessing.Process):
  """Class that defines the multi-processing task.

  Attributes:
    identifier: a string containing the identifier of the task.
    session_identifier: a string containing the identifier of the session
                        the task is part of.
    path_spec (dfvfs.PathSpec): path specification.
  """

  def __init__(self, session_identifier):
    """Initializes the task.

    Args:
      session_identifier: a string containing the identifier of the session
                          the task is part of.
    """
    super(MultiProcessTask, self).__init__(**kwargs)
    self.identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    self.path_spec = None
    self.session_identifier = session_identifier


class MultiProcessBaseProcess(multiprocessing.Process):
  """Class that defines the multi-processing process interface.

  Attributes:
    rpc_port (int): port number of the process status RPC server.
  """

  _NUMBER_OF_RPC_SERVER_START_ATTEMPTS = 14
  _PROCESS_JOIN_TIMEOUT = 5.0

  def __init__(self, process_type, enable_sigsegv_handler=False, **kwargs):
    """Initializes the process object.

    Args:
      process_type (str): process type.
      enable_sigsegv_handler (bool): True if the SIGSEGV handler should
                                     be enabled.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessBaseProcess, self).__init__(**kwargs)
    self._enable_sigsegv_handler = enable_sigsegv_handler
    self._original_sigsegv_handler = None
    # TODO: check if this can be replaced by self.pid or does this only apply
    # to the parent process?
    self._pid = None
    self._rpc_server = None
    self._status_is_running = False
    self._type = process_type

    # We need to share the RPC port number with the engine process.
    self.rpc_port = multiprocessing.Value(u'I', 0)

  @abc.abstractmethod
  def _GetStatus(self):
    """Returns a status dictionary."""

  @abc.abstractmethod
  def _Main(self):
    """The process main loop.

    This method is called when the process is ready to start. A sub class
    should override this method to do the necessary actions in the main loop.
    """

  def _OnCriticalError(self):
    """The process on critical error handler.

    This method is called when the process encountered a critical error e.g.
    a segfault. A sub class should override this method to do the necessary
    actions before the original critical error signal handler it called.

    Be aware that the state of the process should not be trusted a significant
    part of memory could have been overwritten before a segfault. This callback
    is primarily intended to salvage what we need to troubleshoot the error.
    """
    return

  def _SigSegvHandler(self, unused_signal_number, unused_stack_frame):
    """Signal handler for the SIGSEGV signal.

    Args:
      signal_number: Numeric representation of the signal.
      stack_frame: The current stack frame (instance of frame object) or None.
    """
    self._OnCriticalError()

    # Note that the original SIGSEGV handler can be 0.
    if self._original_sigsegv_handler is not None:
      # Let the original SIGSEGV handler take over.
      signal.signal(signal.SIGSEGV, self._original_sigsegv_handler)
      os.kill(self._pid, signal.SIGSEGV)

  def _SigTermHandler(self, unused_signal_number, unused_stack_frame):
    """Signal handler for the SIGTERM signal.

    Args:
      signal_number: Numeric representation of the signal.
      stack_frame: The current stack frame (instance of frame object) or None.
    """
    self.SignalAbort()

  def _StartProcessStatusRPCServer(self):
    """Starts the process status RPC server."""
    if self._rpc_server:
      return

    self._rpc_server = xmlrpc.XMLProcessStatusRPCServer(self._GetStatus)

    hostname = u'localhost'

    # Try the PID as port number first otherwise pick something random
    # between 1024 and 60000.
    if self._pid < 1024 or self._pid > 60000:
      port = random.randint(1024, 60000)
    else:
      port = self._pid

    if not self._rpc_server.Start(hostname, port):
      port = 0
      for _ in range(self._NUMBER_OF_RPC_SERVER_START_ATTEMPTS):
        port = random.randint(1024, 60000)
        if self._rpc_server.Start(hostname, port):
          break

        port = 0

    if not port:
      logging.error((
          u'Unable to start a process status RPC server for {0!s} '
          u'(PID: {1:d})').format(self._name, self._pid))
      self._rpc_server = None
      return

    self.rpc_port.value = port

    logging.debug(
        u'Process: {0!s} process status RPC server started'.format(self._name))

  def _StopProcessStatusRPCServer(self):
    """Stops the process status RPC server."""
    if not self._rpc_server:
      return

    # Make sure the engine gets one more status update so it knows
    # the worker has completed.
    self._WaitForStatusNotRunning()

    self._rpc_server.Stop()
    self._rpc_server = None
    self.rpc_port.value = 0

    logging.debug(
        u'Process: {0!s} process status RPC server stopped'.format(self._name))

  def _WaitForStatusNotRunning(self):
    """Waits for the status is running to change to false."""
    # We wait slightly longer than the status check sleep time.
    time.sleep(2.0)
    time_slept = 2.0
    while self._status_is_running:
      time.sleep(0.5)
      time_slept += 0.5
      if time_slept >= self._PROCESS_JOIN_TIMEOUT:
        break

  @property
  def name(self):
    """The process name."""
    return self._name

  @property
  def type(self):
    """The process type."""
    return self._type

  # This method is part of the multiprocessing.Process interface hence
  # its name does not follow the style guide.
  def run(self):
    """Runs the process."""
    # Prevent the KeyboardInterrupt being raised inside the process.
    # This will prevent a process to generate a traceback when interrupted.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # A SIGTERM signal handler is necessary to make sure IPC is cleaned up
    # correctly on terminate.
    signal.signal(signal.SIGTERM, self._SigTermHandler)

    # A SIGSEGV signal handler is necessary to try to indicate where
    # worker failed.
    # WARNING the SIGSEGV handler will deadlock the process on a real segfault.
    if self._enable_sigsegv_handler:
      self._original_sigsegv_handler = signal.signal(
          signal.SIGSEGV, self._SigSegvHandler)

    self._pid = os.getpid()

    # We need to set the is running status explicitly to True in case
    # the process completes before the engine is able to determine
    # the status of the process, e.g. in the unit tests.
    self._status_is_running = True

    logging.debug(
        u'Process: {0!s} (PID: {1:d}) started'.format(self._name, self._pid))

    self._StartProcessStatusRPCServer()

    self._Main()

    self._StopProcessStatusRPCServer()

    logging.debug(
        u'Process: {0!s} (PID: {1:d}) stopped'.format(self._name, self._pid))

    self._status_is_running = False

  @abc.abstractmethod
  def SignalAbort(self):
    """Signals the process to abort."""


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
      pid (int): a process ID (PID).

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
          u'type': process.type,
      }

    if status_indicator == definitions.PROCESSING_STATUS_ERROR:
      path_spec = process_status.get(u'path_spec', None)
      if path_spec:
        self._processing_status.error_path_specs.append(path_spec)

    self._UpdateProcessingStatus(pid, process_status)

    if status_indicator not in (
        definitions.PROCESSING_STATUS_COMPLETED,
        definitions.PROCESSING_STATUS_INITIALIZED,
        definitions.PROCESSING_STATUS_RUNNING,
        definitions.PROCESSING_STATUS_PARSING,
        definitions.PROCESSING_STATUS_HASHING):

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
      if process.type == definitions.PROCESS_TYPE_WORKER:
        number_of_events = process_status.get(u'number_of_events', 0)
        number_of_pathspecs = process_status.get(
            u'consumed_number_of_path_specs', 0)
        logging.debug((
            u'Process {0:s} (PID: {1:d}) has completed its processing. '
            u'Total of {2:d} events extracted from {3:d} pathspecs').format(
                process.name, pid, number_of_events, number_of_pathspecs))

      self._StopMonitoringProcess(pid)

    elif self._show_memory_usage:
      self._LogMemoryUsage(pid)

  def _CheckStatusWorkerProcesses(self):
    """Checks status of the worker processes.

    Raises:
      EngineAbort: when all the worker are idle.
    """
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
      task = MultiProcessTask(self._session_identifier)
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
    """Processes the sources and extracts event objects.

    Args:
      source_path_specs: a list of path specifications (instances of
                         dfvfs.PathSpec) of the sources to process.
      storage_writer: a storage writer object (instance of StorageWriter).
      filter_find_specs: optional list of filter find specifications (instances
                         of dfvfs.FindSpec).

    Returns:
      A string containing the processing status.
    """
    self._processing_status.UpdateForemanStatus(
        u'Main', u'Initializing', self._pid,
        definitions.PROCESSING_STATUS_RUNNING, u'', 0, 0, 0, 0)
    self._UpdateStatus()

    path_spec_extractor = extractors.PathSpecExtractor(self._resolver_context)

    produced_number_of_sources = 0
    for path_spec in path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=filter_find_specs,
        recurse_file_system=False):
      if self._abort:
        break

      # TODO: determine if event sources should be DataStream or FileEntry
      # or both.
      event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
      storage_writer.AddEventSource(event_source)

      produced_number_of_sources += 1

      self._processing_status.UpdateForemanStatus(
          u'Main', u'Collecting', self._pid,
          definitions.PROCESSING_STATUS_RUNNING, u'', 0,
          produced_number_of_sources, 0, 0)
      self._UpdateStatus()

    task_storage_glob = os.path.join(
        self._storage_writer._task_storage_path, u'*.plaso')

    self._new_event_sources = True
    self._number_of_consumed_sources = 0
    while self._new_event_sources:
      if self._abort:
        return

      # TODO: flushing the storage writer here for now to make sure the event
      # sources are written to disk. Remove this during phased processing
      # refactor.
      storage_writer.ForceFlush()

      self._collector_active = True
      self._new_event_sources = False
      self._StartCollectorThread()

      # TODO: change status check.
      self._CheckStatusWorkerProcesses()

      # TODO: start thread that monitors for new task files.

      while self._collector_active and len(self._tasks):
        self._processing_status.UpdateForemanStatus(
            u'Main', u'Storage', self._pid,
            definitions.PROCESSING_STATUS_RUNNING, u'',
            self._number_of_consumed_sources, produced_number_of_sources,
            0, 0)
        self._CheckStatusWorkerProcesses()
        self._UpdateStatus()

        # TODO: check if task is done.

        # TODO: move task storage merge into separate thread.
        # pylint: disable=protected-access
        for task_storage_file in glob.glob(task_storage_glob):
          storage_reader = storage_zip_file.ZIPStorageFileReader(task_storage_file)
          self._storage_writer.MergeFromStorage(storage_reader)

          # Force close the storage reader so we can remove the file.
          storage_reader.Close()
          os.remove(task_storage_file)

        time.sleep(self._STATUS_CHECK_SLEEP)

      self._StopCollectorThread()

      self._processing_status.UpdateForemanStatus(
          u'Main', u'Idle', self._pid,
          definitions.PROCESSING_STATUS_RUNNING,
          u'',
          self._number_of_consumed_sources, produced_number_of_sources,
          0, 0)
      self._CheckStatusWorkerProcesses()
      self._UpdateStatus()

    if self._abort:
      status = u'Aborted'
      process_status = definitions.PROCESSING_STATUS_ABORTED
    else:
      status = u'Completed'
      process_status = definitions.PROCESSING_STATUS_COMPLETED

    self._processing_status.UpdateForemanStatus(
        u'Main', status, self._pid, process_status, u'',
        self._number_of_consumed_sources, produced_number_of_sources,
        0, 0)
    self._UpdateStatus()

    return process_status

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
    if self._use_zeromq:
      logging.debug(u'Closing ZeroMQ storage queues.')
    else:
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
    if isinstance(self._task_queue, MultiProcessingQueue):
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
      pid (int): process identifier (PID).
      process_status (dict): process status values.

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    self._RaiseIfNotRegistered(pid)

    if not process_status:
      return

    process = self._processes_per_pid[pid]
    process_information = self._process_information_per_pid[pid]

    process_type = process_status.get(u'type', None)
    processing_status = process_status.get(u'processing_status', None)

    if process_type == definitions.PROCESS_TYPE_WORKER:
      self._RaiseIfNotMonitored(pid)

      consumed_number_of_events = process_status.get(
          u'consumed_number_of_events', 0)
      consumed_number_of_sources = process_status.get(
          u'consumed_number_of_sources', 0)
      display_name = process_status.get(u'display_name', u'')
      produced_number_of_events = process_status.get(
          u'produced_number_of_events', 0)
      produced_number_of_sources = process_status.get(
          u'produced_number_of_sources', 0)

      self._processing_status.UpdateWorkerStatus(
          process.name, u'Extracting', pid, processing_status, display_name,
          consumed_number_of_sources, produced_number_of_sources,
          consumed_number_of_events, produced_number_of_events)

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
      self._task_queue = MultiProcessingQueue(
          maximum_number_of_queued_items=self._maximum_number_of_queued_items)

    else:
      task_outbound_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
          delay_open=True, name=u'Task queue', buffer_timeout_seconds=300)
      self._task_queue = task_outbound_queue

      # The ZeroMQ backed queue must be started first, so we can save its port.
      self._task_queue.name = u'Task queue'
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
    _ = self._ProcessSources(
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


class MultiProcessWorkerProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing worker process."""

  def __init__(
      self, task_queue, storage_writer, knowledge_base, session_identifier,
      worker_number, enable_debug_output=False, enable_profiling=False,
      filter_object=None, hasher_names_string=None, mount_path=None,
      parser_filter_expression=None, process_archive_files=False,
      profiling_sample_rate=1000, profiling_type=u'all', text_prepend=None,
      **kwargs):
    """Initializes the process object.

    Args:
      task_queue: the task queue object (instance of MultiProcessingQueue).
      storage_writer: a storage writer object (instance of StorageWriter).
      knowledge_base: a knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
      session_identifier: a string containing the identifier of the session.
      worker_number: a number that identifies the worker.
      enable_debug_output: optional boolean value to indicate if the debug
                           output should be enabled.
      enable_profiling: optional boolean value to indicate if profiling should
                        be enabled.
      filter_object: optional filter object (instance of objectfilter.Filter).
      hasher_names_string: optional comma separated string of names of
                           hashers to enable enable.
      mount_path: optional string containing the mount path. The default
                  is None.
      parser_filter_expression: optional string containing the parser filter
                                expression, where None represents all parsers
                                and plugins.
      process_archive_files: optional boolean value to indicate if the worker
                             should scan for file entries inside files.
      profiling_sample_rate: optional integer indicating the profiling sample
                             rate. The value contains the number of files
                             processed. The default value is 1000.
      profiling_type: optional profiling type.
      text_prepend: optional string that contains the text to prepend to every
                    event object.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessWorkerProcess, self).__init__(
        definitions.PROCESS_TYPE_WORKER, **kwargs)
    self._abort = False
    self._buffer_size = 0
    self._critical_error = False
    self._enable_debug_output = enable_debug_output
    self._extraction_worker = None
    self._knowledge_base = knowledge_base
    self._number_of_consumed_path_specs = 0
    self._session_identifier = session_identifier
    self._status = definitions.PROCESSING_STATUS_INITIALIZED
    self._storage_writer = storage_writer
    self._task_queue = task_queue
    self._worker_number = worker_number

    # Attributes for profiling.
    self._enable_profiling = enable_profiling
    self._profiling_sample_rate = profiling_sample_rate
    self._profiling_type = profiling_type

    # TODO: clean this up with the implementation of a task based
    # multi-processing approach.
    self._filter_object = filter_object
    self._hasher_names_string = hasher_names_string
    self._mount_path = mount_path
    self._parser_filter_expression = parser_filter_expression
    self._process_archive_files = process_archive_files
    self._text_prepend = text_prepend

  def _GetStatus(self):
    """Returns a status dictionary."""
    if self._parser_mediator:
      number_of_produced_events = (
          self._parser_mediator.number_of_produced_events)
      number_of_produced_sources = (
          self._parser_mediator.number_of_produced_sources)
    else:
      number_of_produced_events = 0
      number_of_produced_sources = 0

    # TODO: add number of consumed events.
    status = {
        u'consumed_number_of_events': 0,
        u'consumed_number_of_sources': self._number_of_consumed_path_specs,
        u'display_name': self._extraction_worker.current_display_name,
        u'identifier': self._name,
        u'processing_status': self._status,
        u'produced_number_of_events': number_of_produced_events,
        u'produced_number_of_sources': number_of_produced_sources,
        u'type': definitions.PROCESS_TYPE_WORKER}

    if self._critical_error:
      # Note seem unable to pass objects here.
      current_path_spec = self._extraction_worker.current_path_spec
      status[u'path_spec'] = current_path_spec.comparable
      status[u'processing_status'] = definitions.PROCESSING_STATUS_ERROR

    self._status_is_running = status.get(u'is_running', False)
    return status

  def _ProcessTask(self, task):
    """Processes a task.

    Args:
      task (MultiProcessTask): task.
    """
    storage_writer = self._storage_writer.CreateTaskStorageWriter(
        task.identifier)

    if self._enable_profiling:
      storage_writer.EnableProfiling(profiling_type=self._profiling_type)

    storage_writer.Open()

    task_start = tasks.TaskStart(self._session_identifier)

    try:
      storage_writer.WriteTaskStart(task_start)

      # TODO: add support for more task types.
      self._extraction_worker.ProcessPathSpec(
          self._parser_mediator, task.path_spec)
      self._number_of_consumed_path_specs += 1

    finally:
      # TODO: on abort use WriteTaskAborted instead of completion?
      storage_writer.WriteTaskCompletion()
      storage_writer.Close()

      if self._enable_profiling:
        storage_writer.DisableProfiling()

  def _Main(self):
    """The main loop."""
    # We need to initialize the parser and hasher objects after the process
    # has forked otherwise on Windows the "fork" will fail with
    # a PickleError for Python modules that cannot be pickled.
    self._parser_mediator = parsers_mediator.ParserMediator(
        storage_writer, self._knowledge_base)

    if self._filter_object:
      self._parser_mediator.SetFilterObject(self._filter_object)

    if self._mount_path:
      self._parser_mediator.SetMountPath(self._mount_path)

    if self._text_prepend:
      self._parser_mediator.SetTextPrepend(self._text_prepend)

    # We need a resolver context per process to prevent multi processing
    # issues with file objects stored in images.
    resolver_context = context.Context()

    self._extraction_worker = worker.EventExtractionWorker(
        resolver_context,
        parser_filter_expression=self._parser_filter_expression,
        process_archive_files=self._process_archive_files)

    # TODO: differentiate between debug output and debug mode.
    self._extraction_worker.SetEnableDebugMode(self._enable_debug_output)

    if hasher_names_string:
      self._extraction_worker.SetHashers(hasher_names_string)

    if self._enable_profiling:
      self._extraction_worker.EnableProfiling(
          profiling_sample_rate=self._profiling_sample_rate,
          profiling_type=self._profiling_type)

    self._extraction_worker.ProfilingStart(self._name)

    logging.debug(u'Worker: {0!s} (PID: {1:d}) started'.format(
        self._name, self._pid))

    self._status = definitions.PROCESSING_STATUS_RUNNING

    try:
      logging.debug(
          u'{0!s} (PID: {1:d}) started monitoring task queue.'.format(
              self._name, self._pid))

      while not self._abort:
        try:
          task = self._task_queue.PopItem()
        except (errors.QueueClose, errors.QueueEmpty) as exception:
          logging.debug(u'ConsumeItems exiting with exception {0:s}.'.format(
              type(exception)))
          break

        if isinstance(task, plaso_queue.QueueAbort):
          logging.debug(u'ConsumeItems exiting, dequeued QueueAbort object.')
          break

        self._ProcessTask(task)

      logging.debug(
          u'{0!s} (PID: {1:d}) stopped monitoring task queue.'.format(
              self._name, self._pid))

    except Exception as exception:  # pylint: disable=broad-except
      logging.warning(
          u'Unhandled exception in worker: {0!s} (PID: {1:d}).'.format(
              self._name, self._pid))
      logging.exception(exception)

      self._abort = True

    self._extraction_worker.ProfilingStop()
    self._extraction_worker = None
    self._parser_mediator = None

    if self._abort:
      self._status = definitions.PROCESSING_STATUS_ABORTED
    else:
      self._status = definitions.PROCESSING_STATUS_COMPLETED

    logging.debug(u'Extraction worker: {0!s} (PID: {1:d}) stopped'.format(
        self._name, self._pid))

    if isinstance(self._task_queue, MultiProcessingQueue):
      self._task_queue.Close(abort=True)
    else:
      self._task_queue.Close()

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
    self._extraction_worker.SignalAbort()
    self._parser_mediator.SignalAbort()


class MultiProcessingQueue(plaso_queue.Queue):
  """Class that defines the multi-processing queue."""

  def __init__(self, maximum_number_of_queued_items=0, timeout=None):
    """Initializes the multi-processing queue object.

    Args:
      maximum_number_of_queued_items: The maximum number of queued items.
                                      The default is 0, which represents
                                      no limit.
      timeout: Optional floating point number of seconds for the get to
               time out. The default is None, which means the get will
               block until a new item is put onto the queue.
    """
    super(MultiProcessingQueue, self).__init__()
    self._timeout = timeout

    # maxsize contains the maximum number of items allowed to be queued,
    # where 0 represents unlimited.

    # We need to check that we aren't asking for a bigger queue than the
    # platform supports, which requires access to this protected member.
    # pylint: disable=protected-access
    queue_max_length = multiprocessing._multiprocessing.SemLock.SEM_VALUE_MAX
    # pylint: enable=protected-access

    if maximum_number_of_queued_items > queue_max_length:
      logging.warning((
          u'Requested maximum queue size: {0:d} is larger than the maximum '
          u'size supported by the system. Defaulting to: {1:d}').format(
              maximum_number_of_queued_items, queue_max_length))
      maximum_number_of_queued_items = queue_max_length

    # This queue appears not to be FIFO.
    self._queue = multiprocessing.Queue(maxsize=maximum_number_of_queued_items)

  def Open(self):
    """Opens the queue."""
    pass

  # pylint: disable=arguments-differ
  def Close(self, abort=False):
    """Closes the queue.

    This needs to be called from any process or thread putting items onto
    the queue.

    Args:
      abort: optional boolean to indicate the close is issued on abort.
    """
    if abort:
      # Prevent join_thread() from blocking.
      self._queue.cancel_join_thread()

    self._queue.close()
    self._queue.join_thread()

  def Empty(self):
    """Empties the queue."""
    try:
      while True:
        self._queue.get(False)
    except Queue.Empty:
      pass

  def IsEmpty(self):
    """Determines if the queue is empty."""
    return self._queue.empty()

  def PushItem(self, item, block=True):
    """Pushes an item onto the queue.

    Args:
      block: boolean value to indicate put should block
             if the queue is full.
    """
    try:
      self._queue.put(item, block=block)

    # Queue.Full can be raised if block is False.
    # Since this should only be used in the abort code path
    # the exception is ignored.
    except Queue.Full:
      pass

  def PopItem(self):
    """Pops an item off the queue.

    Raises:
      QueueClose: if the queue has already been closed.
      QueueEmpty: if no item could be retrieved from the queue within the
                  specified timeout.
    """
    try:
      # If no timeout is specified the queue will block if empty otherwise
      # a Queue.Empty exception is raised.
      return self._queue.get(timeout=self._timeout)
    except KeyboardInterrupt:
      raise errors.QueueClose
    # If close() is called on the multiprocessing.Queue while it is blocking
    # on get() it will raise IOError.
    except IOError:
      raise errors.QueueClose
    except Queue.Empty:
      raise errors.QueueEmpty
