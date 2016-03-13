# -*- coding: utf-8 -*-
"""The multi-process processing engine."""

import abc
import ctypes
import logging
import multiprocessing
import os
import Queue
import random
import signal
import sys
import time

from dfvfs.resolver import context

from plaso.engine import collector
from plaso.engine import engine
from plaso.engine import queue
from plaso.engine import worker
from plaso.engine import zeromq_queue
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import process_info
from plaso.multi_processing import xmlrpc
from plaso.parsers import mediator as parsers_mediator


class MultiProcessBaseProcess(multiprocessing.Process):
  """Class that defines the multi-processing process interface.

  Attributes:
    rpc_port: the port number of the process status RPC server.
  """

  _NUMBER_OF_RPC_SERVER_START_ATTEMPTS = 14
  _PROCESS_JOIN_TIMEOUT = 5.0

  def __init__(self, process_type, enable_sigsegv_handler=False, **kwargs):
    """Initializes the process object.

    Args:
      process_type: the process type.
      enable_sigsegv_handler: optional boolean value to indicate the SIGSEGV
                              handler should be enabled.
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
    self.rpc_port = multiprocessing.Value('I', 0)

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


class MultiProcessCollectorProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing collector process."""

  def __init__(
      self, stop_collector_event, source_path_specs, path_spec_queue,
      filter_find_specs=None, include_directory_stat=True, **kwargs):
    """Initializes the process object.

    Args:
      stop_collector_event: the stop process event (instance of
                            multiprocessing.Event). The collector
                            should exit after this event is set.
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      path_spec_queue: the path specification queue object (instance of
                       MultiProcessingQueue).
      filter_find_specs: Optional list of filter find specifications (instances
                         of dfvfs.FindSpec).
      include_directory_stat: Optional boolean value to indicate whether
                              directory stat information should be collected.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessCollectorProcess, self).__init__(
        definitions.PROCESS_TYPE_COLLECTOR, **kwargs)
    resolver_context = context.Context()

    self._collector = collector.Collector(
        path_spec_queue, resolver_context=resolver_context)
    self._path_spec_queue = path_spec_queue
    self._path_spec_queue_port = None
    self._source_path_specs = source_path_specs
    self._stop_collector_event = stop_collector_event
    self._collector.SetCollectDirectoryMetadata(include_directory_stat)

    if filter_find_specs:
      self._collector.SetFilter(filter_find_specs)

  def _GetStatus(self):
    """Returns a status dictionary."""
    status = self._collector.GetStatus()
    status[u'path_spec_queue_port'] = self._path_spec_queue_port
    self._status_is_running = status.get(u'is_running', False)
    return status

  def _Main(self):
    """The main loop."""
    logging.debug(u'Collector (PID: {0:d}) started'.format(self._pid))

    # The ZeroMQ backed queue must be started first, so we can save its port.
    if isinstance(self._path_spec_queue, zeromq_queue.ZeroMQQueue):
      self._path_spec_queue.name = u'Collector pathspec'
      self._path_spec_queue.Open()
      self._path_spec_queue_port = self._path_spec_queue.port

    abort = False
    try:
      logging.debug(u'Collector starting collection.')
      self._collector.Collect(self._source_path_specs)

    except Exception as exception:
      logging.warning(
          u'Unhandled exception in collector (PID: {0:d}).'.format(self._pid))
      logging.exception(exception)
      abort = True

    self._path_spec_queue.Close()

    logging.debug(u'Collector (PID: {0:d}) stopped'.format(self._pid))

    # The collector will typically collect the path specifications and
    # exit. However multiprocessing.Queue will start a separate thread
    # that blocks on close until every item is read from the queue. This
    # is necessary since the queue uses a pipe under the hood. However
    # this behavior causes unwanted side effect for the abort code paths
    # hence we have the process wait for the stop process event and then
    # close the queue without the separate blocking thread.

    if not abort:
      logging.debug(u'Collector waiting for stop event.')
      self._stop_collector_event.wait()

    self._path_spec_queue.Close(abort=True)

  def SignalAbort(self):
    """Signals the process to abort."""
    self._collector.SignalAbort()


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
      maximum_number_of_queued_items: Optional maximum number of queued items.
                                      The default is 0, which represents
                                      no limit.
      use_zeromq: Optional boolean to indicate whether to use ZeroMQ for
                  queuing. If False, the multiprocessing queue will be used.
    """
    self._use_zeromq = use_zeromq
    if self._use_zeromq:
      path_spec_outbound_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
          delay_open=True, name=u'Pathspec inbound', buffer_timeout_seconds=300)
      path_spec_queue = path_spec_outbound_queue
      event_object_inbound_queue = zeromq_queue.ZeroMQBufferedPullBindQueue(
          delay_open=True, name=u'Event object inbound', timeout_seconds=60,
          buffer_max_size=10000, linger_seconds=0)
      event_object_queue = event_object_inbound_queue
      parse_error_inbound_queue = zeromq_queue.ZeroMQBufferedPullBindQueue(
          delay_open=True, name=u'Parse error inbound', timeout_seconds=60,
          buffer_max_size=10000, linger_seconds=0)
      parse_error_queue = parse_error_inbound_queue
    else:
      path_spec_queue = MultiProcessingQueue(
          maximum_number_of_queued_items=maximum_number_of_queued_items)
      event_object_queue = MultiProcessingQueue(
          maximum_number_of_queued_items=maximum_number_of_queued_items)
      parse_error_queue = MultiProcessingQueue(
          maximum_number_of_queued_items=maximum_number_of_queued_items)

    super(MultiProcessEngine, self).__init__(
        path_spec_queue, event_object_queue, parse_error_queue)

    self._enable_sigsegv_handler = False
    self._event_object_queue_port = None
    self._extraction_complete_event = None
    self._filter_find_specs = None
    self._filter_object = None
    self._hasher_names_string = None
    self._include_directory_stat = True
    self._last_worker_number = 0
    self._mount_path = None
    self._number_of_extraction_workers = 0
    self._parse_error_queue_port = None
    self._parser_filter_string = None
    self._path_spec_queue_port = None
    self._process_archive_files = False
    self._process_information_per_pid = {}
    self._processes_per_pid = {}
    self._rpc_clients_per_pid = {}
    self._rpc_errors_per_pid = {}
    self._storage_writer_completed = False
    self._show_memory_usage = False
    self._stop_collector_event = None
    self._text_prepend = None

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

  def _CheckStatus(self):
    """Checks status of the monitored processes.

    Returns:
      A boolean indicating whether processing is complete.

    Raises:
      EngineAbort: when all the worker are idle.
    """
    for pid in iter(self._process_information_per_pid.keys()):
      self._CheckProcessStatus(pid)

    extraction_completed = self._processing_status.GetExtractionCompleted()
    if extraction_completed:
      logging.debug(u'Extraction completed.')

    processing_completed = self._processing_status.GetProcessingCompleted()
    if processing_completed and not self._processing_status.error_detected:
      logging.debug(u'Processing completed.')

    if (self._processing_status.WorkersIdle() and
        self._processing_status.StorageWriterIdle()):
      logging.error(u'Workers idle for too long')
      self._processing_status.error_detected = True
      raise errors.EngineAbort(u'Workers idle for too long')

    return extraction_completed, processing_completed

  def _CheckProcessStatus(self, pid):
    """Check status of a specific monitored process and take action on it.

    This method examines the status of a process, and then terminates it,
    signals other processes to terminate or starts a replacement process as
    appropriate.

    Args:
      pid: The process ID (PID).

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

      if process.type == definitions.PROCESS_TYPE_COLLECTOR:
        raise errors.EngineAbort(u'Collector unexpectedly terminated')

      if process.type == definitions.PROCESS_TYPE_STORAGE_WRITER:
        raise errors.EngineAbort(u'Storage writer unexpectedly terminated')

      self._TerminateProcess(pid)

      logging.info(u'Starting replacement worker process for {0:s}'.format(
          process.name))
      worker_process = self._StartExtractionWorkerProcess()
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
      elif process.type == definitions.PROCESS_TYPE_COLLECTOR:
        number_of_pathspecs = process_status.get(
            u'produced_number_of_path_specs', 0)
        logging.debug((
            u'Process {0:s} (PID: {1:d}) has completed its processing. '
            u'Total of {2:d} pathspecs extracted').format(
                process.name, pid, number_of_pathspecs))
      elif process.type == definitions.PROCESS_TYPE_STORAGE_WRITER:
        logging.debug((
            u'Process {0:s} (PID: {1:d}) has completed its processing. '
            u'Total of {2:d} events written').format(
                process.name, pid, process_status.get(u'number_of_events', 0)))

      self._StopMonitoringProcess(pid)

    elif self._show_memory_usage:
      self._LogMemoryUsage(pid)

  def _CloseStorageZeroMQQueues(self):
    """Closes all ZeroMQ queues being used by the storage writer."""
    logging.debug(u'Closing ZeroMQ storage queues.')
    for port in (self._event_object_queue_port, self._parse_error_queue_port):
      terminate_queue = zeromq_queue.ZeroMQPushConnectQueue(
          linger_seconds=0, port=port, timeout_seconds=0, name=u'Termination')
      terminate_queue.PushItem(queue.QueueAbort(), block=False)
      terminate_queue.Close()

  def _CollectorQueueHasBound(self):
    """Checks if the collector has bound to a queue."""
    return self._path_spec_queue_port is not None

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

  def _StartExtractionWorkerProcess(self):
    """Creates, starts and registers an extraction worker process.

    Returns:
      An extraction worker process (instance of
      MultiProcessEventExtractionWorkerProcess).
    """
    process_name = u'Worker_{0:02d}'.format(self._last_worker_number)

    if self._use_zeromq:
      path_spec_queue = zeromq_queue.ZeroMQRequestConnectQueue(
          delay_open=True, port=self._path_spec_queue_port,
          timeout_seconds=2,
          name=u'{0:s} pathspec'.format(process_name),
          linger_seconds=0)
      # The high water mark is set to 2 for these queues so that data
      # doesn't build up in the workers, to prevent data loss in the case
      # that they crash.
      parse_error_queue = zeromq_queue.ZeroMQPushConnectQueue(
          delay_open=True, port=self._parse_error_queue_port,
          name=u'{0:s} parse error'.format(process_name),
          timeout_seconds=20, maximum_items=2)
      event_object_queue = zeromq_queue.ZeroMQPushConnectQueue(
          delay_open=True, port=self._event_object_queue_port,
          name=u'{0:s} event object'.format(process_name),
          timeout_seconds=20, maximum_items=2)
    else:
      parse_error_queue = self._parse_error_queue
      path_spec_queue = self._path_spec_queue
      event_object_queue = self.event_object_queue

    worker_process = MultiProcessEventExtractionWorkerProcess(
        path_spec_queue, event_object_queue,
        parse_error_queue, self.knowledge_base, self._last_worker_number,
        enable_debug_output=self._enable_debug_output,
        enable_profiling=self._enable_profiling,
        enable_sigsegv_handler=self._enable_sigsegv_handler,
        filter_object=self._filter_object,
        hasher_names_string=self._hasher_names_string,
        mount_path=self._mount_path, name=process_name,
        parser_filter_string=self._parser_filter_string,
        process_archive_files=self._process_archive_files,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type, text_prepend=self._text_prepend)

    worker_process.start()
    self._last_worker_number += 1

    self._RegisterProcess(worker_process)

    return worker_process

  def _StopExtractionProcesses(self, abort=False):
    """Stops the extraction processes.

    Args:
      abort: optional boolean to indicate the stop is issued on abort.
    """
    logging.debug(u'Stopping extraction processes.')
    self._StopProcessMonitoring()
    # We can stop the collector and storage writer now.
    self._stop_collector_event.set()
    self._extraction_complete_event.set()

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
      self._path_spec_queue.Empty()
      self.event_object_queue.Empty()
      self._parse_error_queue.Empty()
      # Wake the processes to make sure that they are not blocking
      # waiting for new items.
      for _ in range(self._number_of_extraction_workers):
        self._path_spec_queue.PushItem(queue.QueueAbort(), block=False)
      self.event_object_queue.PushItem(queue.QueueAbort(), block=False)
      self._parse_error_queue.PushItem(queue.QueueAbort(), block=False)
    else:
      self._CloseStorageZeroMQQueues()

    # Try waiting for the processes to exit normally.
    self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)

    if not abort:
      # The storage writer process sometimes needs some additional time to
      # exit normally.
      time.sleep(0.5)

      # Check if the processes are still alive and terminate them if necessary.
      self._AbortTerminate()
      self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)

    # For Multiprocessing queues, set abort to True to stop queue.join_thread()
    # from blocking.
    extraction_queues = [
        self._path_spec_queue, self.event_object_queue, self._parse_error_queue]
    for extraction_queue in extraction_queues:
      if isinstance(extraction_queue, MultiProcessingQueue):
        extraction_queue.Close(abort=True)

    if abort:
      # Kill any remaining processes, which can be necessary if
      # the collector dies.
      self._AbortKill()

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

  def _StorageQueuesBound(self):
    """Checks if the storage queues are bound to ports.

    Returns:
      True if both the event_object queue and the parse_error queues are bound
      to ports. False otherwise.
    """
    return (self._event_object_queue_port is not None and
            self._parse_error_queue_port is not None)

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
      pid: The process identifier.
      process_status: A process status dictionary.

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    self._RaiseIfNotRegistered(pid)

    if not process_status:
      return

    process = self._processes_per_pid[pid]
    process_information = self._process_information_per_pid[pid]

    process_type = process_status.get(u'type', None)
    status_indicator = process_status.get(u'processing_status', None)

    if process_type == definitions.PROCESS_TYPE_COLLECTOR:
      produced_number_of_path_specs = process_status.get(
          u'produced_number_of_path_specs', 0)

      self._processing_status.UpdateCollectorStatus(
          process.name, pid, produced_number_of_path_specs, status_indicator,
          process_information.status)

    elif process_type == definitions.PROCESS_TYPE_STORAGE_WRITER:
      number_of_events = process_status.get(u'number_of_events', 0)

      self._processing_status.UpdateStorageWriterStatus(
          process.name, pid, number_of_events, status_indicator,
          process_information.status)

    elif process_type == definitions.PROCESS_TYPE_WORKER:
      self._RaiseIfNotMonitored(pid)

      consumed_number_of_path_specs = process_status.get(
          u'consumed_number_of_path_specs', 0)
      display_name = process_status.get(u'display_name', u'')
      number_of_events = process_status.get(u'number_of_events', 0)
      produced_number_of_path_specs = process_status.get(
          u'produced_number_of_path_specs', 0)

      self._processing_status.UpdateExtractionWorkerStatus(
          process.name, pid, display_name, number_of_events,
          consumed_number_of_path_specs, produced_number_of_path_specs,
          status_indicator, process_information.status)

  def ProcessSources(
      self, source_path_specs, storage_writer, enable_sigsegv_handler=False,
      filter_find_specs=None, filter_object=None, hasher_names_string=None,
      include_directory_stat=True, mount_path=None,
      number_of_extraction_workers=0, parser_filter_string=None,
      process_archive_files=False, status_update_callback=None,
      show_memory_usage=False, text_prepend=None):
    """Processes the sources and extract event objects.

    Args:
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      storage_writer: A storage writer object (instance of BaseStorageWriter).
      enable_sigsegv_handler: optional boolean value to indicate the SIGSEGV
                              handler should be enabled.
      filter_find_specs: Optional list of filter find specifications (instances
                         of dfvfs.FindSpec).
      filter_object: Optional filter object (instance of objectfilter.Filter).
      hasher_names_string: Optional comma separated string of names of
                           hashers to enable enable.
      include_directory_stat: Optional boolean value to indicate whether
                              directory stat information should be collected.
      mount_path: Optional string containing the mount path. The default
                  is None.
      number_of_extraction_workers: Optional number of extraction worker
                                    processes. The default is 0 which means
                                    the function will determine the suitable
                                    number.
      parser_filter_string: Optional parser filter string.
      process_archive_files: Optional boolean value to indicate if the worker
                             should scan for file entries inside files.
      status_update_callback: Optional callback function for status updates.
      show_memory_usage: Optional boolean value to indicate memory information
                         should be included in logging.
      text_prepend: Optional string that contains the text to prepend to every
                    event object.

    Returns:
      The processing status (instance of ProcessingStatus).
    """
    if number_of_extraction_workers < 1:
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

      number_of_extraction_workers = cpu_count

    self._enable_sigsegv_handler = enable_sigsegv_handler
    self._number_of_extraction_workers = number_of_extraction_workers
    self._show_memory_usage = show_memory_usage

    # Keep track of certain values so we can spawn new extraction workers.
    self._filter_find_specs = filter_find_specs
    self._filter_object = filter_object
    self._hasher_names_string = hasher_names_string
    self._include_directory_stat = include_directory_stat
    self._mount_path = mount_path
    self._parser_filter_string = parser_filter_string
    self._process_archive_files = process_archive_files
    self._text_prepend = text_prepend

    logging.debug(u'Starting processes.')

    # Start the storage writer first, as we need it to start up and bind its
    # queues to ports before we can start the workers.
    self._extraction_complete_event = multiprocessing.Event()

    storage_writer_process = MultiProcessStorageWriterProcess(
        self.event_object_queue, self._extraction_complete_event,
        self._parse_error_queue, storage_writer,
        enable_sigsegv_handler=self._enable_sigsegv_handler,
        name=u'StorageWriter')
    storage_writer_process.start()
    self._RegisterProcess(storage_writer_process)
    self._StartMonitoringProcess(storage_writer_process.pid)

    if self._use_zeromq:
      self._GetStorageQueuePorts(storage_writer_process)

   # Next start the collector, as we needs its port number for the workers as
   # well.
    self._stop_collector_event = multiprocessing.Event()
    collector_process = MultiProcessCollectorProcess(
        self._stop_collector_event, source_path_specs, self._path_spec_queue,
        enable_sigsegv_handler=self._enable_sigsegv_handler,
        filter_find_specs=self._filter_find_specs,
        include_directory_stat=self._include_directory_stat, name=u'Collector')
    collector_process.start()
    self._RegisterProcess(collector_process)
    self._StartMonitoringProcess(collector_process.pid)

    if self._use_zeromq:
      self._GetCollectorStoragePorts(collector_process)

    # Finally, start the workers.
    for _ in range(number_of_extraction_workers):
      extraction_process = self._StartExtractionWorkerProcess()
      self._StartMonitoringProcess(extraction_process.pid)

    try:
      logging.debug(u'Processing started.')

      time.sleep(self._STATUS_CHECK_SLEEP)
      extraction_completed, processing_completed = self._CheckStatus()
      while not processing_completed:
        if status_update_callback:
          status_update_callback(self._processing_status)
        if extraction_completed:
          self._extraction_complete_event.set()
        time.sleep(self._STATUS_CHECK_SLEEP)
        extraction_completed, processing_completed = self._CheckStatus()

      # If the storage writer finishes writing very soon after the workers,
      # we may not set the event before the storage writer finishes, so set it
      # explicitly here.
      self._extraction_complete_event.set()

      logging.debug(u'Processing stopped.')
    except errors.EngineAbort as exception:
      logging.warning(
          u'Processing aborted with engine error: {0:s}.'.format(exception))

    except Exception as exception:
      logging.error(
          u'Processing aborted with error: {0:s}.'.format(exception))
      self._processing_status.error_detected = True

    self._StopExtractionProcesses(abort=self._processing_status.error_detected)

    return self._processing_status

  def _GetCollectorStoragePorts(self, collector_process):
    """Ensures that port number for the collector pathspec queue is captured.

    Args:
      collector_process: the collector process object (instance of
                         MultiProcessCollectorProcess).

    Raises:
      RuntimeError: if the collector is not able to start its queue before the
                    the timeout is reached.
    """
    queue_start_wait_attempts = 0
    while (not self._CollectorQueueHasBound() and
           queue_start_wait_attempts < self._QUEUE_START_WAIT_ATTEMPTS_MAXIMUM):
      status = self._GetProcessStatus(collector_process)
      self._path_spec_queue_port = status[u'path_spec_queue_port']
      queue_start_wait_attempts += 1
      time.sleep(self._QUEUE_START_WAIT)
    if not self._CollectorQueueHasBound():
      raise RuntimeError(u'Collector queue did not bind in time.')

  def _GetStorageQueuePorts(self, storage_writer_process):
    """Ensures that port numbers for the storage writer queues are captured.

    Args:
      storage_writer_process: the storage writer process object (instance of
                              MultiProcessStorageWriterProcess).

    Raises:
      RuntimeError: if the storage writer process is not able to starts its
                    queues before the timeout is reached.
    """
    queue_start_wait_attempts = 0
    while (not self._StorageQueuesBound() and
           queue_start_wait_attempts < self._QUEUE_START_WAIT_ATTEMPTS_MAXIMUM):
      status = self._GetProcessStatus(storage_writer_process)
      self._event_object_queue_port = status[u'event_object_queue_port']
      self._parse_error_queue_port = status[u'parse_error_queue_port']
      queue_start_wait_attempts += 1
      time.sleep(self._QUEUE_START_WAIT)
    if not self._StorageQueuesBound():
      raise RuntimeError(u'Storage queues did not bind in time.')

  def SignalAbort(self):
    """Signals the engine to abort."""
    try:
      self._StopExtractionProcesses(abort=True)

    except KeyboardInterrupt:
      self._AbortKill()

      # The abort can leave the main process unresponsive
      # due to incorrectly finalized IPC.
      self._KillProcess(os.getpid())


class MultiProcessEventExtractionWorkerProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing event extraction worker process."""

  def __init__(
      self, path_spec_queue, event_object_queue, parse_error_queue,
      knowledge_base, worker_number, enable_debug_output=False,
      enable_profiling=False, filter_object=None, hasher_names_string=None,
      mount_path=None, parser_filter_string=None, process_archive_files=False,
      profiling_sample_rate=1000, profiling_type=u'all', text_prepend=None,
      **kwargs):
    """Initializes the process object.

    Args:
      path_spec_queue: the path specification queue object (instance of
                       MultiProcessingQueue).
      event_object_queue: the event object queue object (instance of
                          MultiProcessingQueue).
      parse_error_queue: the parser error queue object (instance of
                         MultiProcessingQueue).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
      worker_number: A number that identifies the worker.
      enable_debug_output: Optional boolean value to indicate if the debug
                           output should be enabled.
      enable_profiling: Optional boolean value to indicate if profiling should
                        be enabled.
      filter_object: Optional filter object (instance of objectfilter.Filter).
      hasher_names_string: Optional comma separated string of names of
                           hashers to enable enable.
      mount_path: Optional string containing the mount path. The default
                  is None.
      parser_filter_string: Optional parser filter string.
      process_archive_files: Optional boolean value to indicate if the worker
                             should scan for file entries inside files.
      profiling_sample_rate: optional integer indicating the profiling sample
                             rate. The value contains the number of files
                             processed. The default value is 1000.
      profiling_type: optional profiling type.
      text_prepend: Optional string that contains the text to prepend to every
                    event object.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessEventExtractionWorkerProcess, self).__init__(
        definitions.PROCESS_TYPE_WORKER, **kwargs)
    self._critical_error = False
    self._enable_debug_output = enable_debug_output
    self._event_object_queue = event_object_queue
    self._event_queue_producer = None
    self._extraction_worker = None
    self._knowledge_base = knowledge_base
    self._parse_error_queue = parse_error_queue
    self._path_spec_queue = path_spec_queue
    self._parse_error_queue_producer = None
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
    self._process_archive_files = process_archive_files
    self._parser_filter_string = parser_filter_string
    self._text_prepend = text_prepend

  def _GetStatus(self):
    """Returns a status dictionary."""
    if not self._extraction_worker:
      status = {}
    else:
      status = self._extraction_worker.GetStatus()

    if self._critical_error:
      # Note seem unable to pass objects here.
      current_path_spec = self._extraction_worker.current_path_spec
      status[u'path_spec'] = current_path_spec.comparable
      status[u'processing_status'] = definitions.PROCESSING_STATUS_ERROR

    self._status_is_running = status.get(u'is_running', False)
    return status

  def _Main(self):
    """The main loop."""
    self._event_queue_producer = queue.ItemQueueProducer(
        self._event_object_queue)
    self._parse_error_queue_producer = queue.ItemQueueProducer(
        self._parse_error_queue)

    parser_mediator = parsers_mediator.ParserMediator(
        self._event_queue_producer, self._parse_error_queue_producer,
        self._knowledge_base)

    # We need a resolver context per process to prevent multi processing
    # issues with file objects stored in images.
    resolver_context = context.Context()

    self._extraction_worker = worker.BaseEventExtractionWorker(
        self._worker_number, self._path_spec_queue, self._event_queue_producer,
        self._parse_error_queue_producer, parser_mediator,
        resolver_context=resolver_context)

    self._extraction_worker.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type)

    self._extraction_worker.SetProcessArchiveFiles(self._process_archive_files)

    if self._filter_object:
      self._extraction_worker.SetFilterObject(self._filter_object)

    if self._mount_path:
      self._extraction_worker.SetMountPath(self._mount_path)

    if self._text_prepend:
      self._extraction_worker.SetTextPrepend(self._text_prepend)

    # We need to initialize the parser and hasher objects after the process
    # has forked otherwise on Windows the "fork" will fail with
    # a PickleError for Python modules that cannot be pickled.
    self._extraction_worker.InitializeParserObjects(
        parser_filter_string=self._parser_filter_string)

    if self._hasher_names_string:
      self._extraction_worker.SetHashers(self._hasher_names_string)

    logging.debug(u'Extraction worker: {0!s} (PID: {1:d}) started'.format(
        self._name, self._pid))

    try:
      self._extraction_worker.Run()

    except Exception as exception:
      logging.warning((
          u'Unhandled exception in extraction worker {0!s} '
          u'(PID: {1:d}).').format(self._name, self._pid))
      logging.exception(exception)

    logging.debug(u'Extraction worker: {0!s} (PID: {1:d}) stopped'.format(
        self._name, self._pid))

    worker_queues = (
        self._path_spec_queue, self._event_object_queue,
        self._parse_error_queue)
    for worker_queue in worker_queues:
      if not isinstance(worker_queue, MultiProcessingQueue):
        worker_queue.Close()
      else:
        worker_queue.Close(abort=True)

  def _OnCriticalError(self):
    """The process on critical error handler."""
    self._critical_error = True
    self._WaitForStatusNotRunning()

  def SignalAbort(self):
    """Signals the process to abort."""
    if self._event_queue_producer:
      self._event_queue_producer.SignalAbort()

    if self._parse_error_queue_producer:
      self._parse_error_queue_producer.SignalAbort()

    if self._extraction_worker:
      self._extraction_worker.SignalAbort()


class MultiProcessStorageWriterProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing storage writer process."""

  def __init__(
      self, event_object_queue, extraction_complete_event, parse_error_queue,
      storage_writer, **kwargs):
    """Initializes the process object.

    Args:
      event_object_queue: the event object queue object (instance of
                          MultiProcessingQueue).
      extraction_complete_event: an Event that, when set, indicates that
                                 extraction is complete.
      parse_error_queue: the parser error queue object (instance of Queue).
      storage_writer: a storage writer object (instance of BaseStorageWriter).
    """
    super(MultiProcessStorageWriterProcess, self).__init__(
        definitions.PROCESS_TYPE_STORAGE_WRITER, **kwargs)
    self._extraction_complete_event = extraction_complete_event
    self._event_object_queue = event_object_queue
    self._event_object_queue_port = None
    self._parse_error_queue = parse_error_queue
    self._parse_error_queue_port = None
    self._storage_writer = storage_writer

  def _GetStatus(self):
    """Returns a status dictionary."""
    status = self._storage_writer.GetStatus()
    status[u'event_object_queue_port'] = self._event_object_queue_port
    status[u'parse_error_queue_port'] = self._parse_error_queue_port
    self._status_is_running = status.get(u'is_running', False)
    return status

  def _Main(self):
    """The main loop."""
    logging.debug(u'Storage writer (PID: {0:d}) started.'.format(self._pid))

    event_queue_is_zeromq = isinstance(
        self._event_object_queue, zeromq_queue.ZeroMQQueue)
    error_queue_is_zeromq = isinstance(
        self._parse_error_queue, zeromq_queue.ZeroMQQueue)

    if event_queue_is_zeromq:
      self._event_object_queue.name = u'Storage writer event'
      self._event_object_queue.Open()
      self._event_object_queue_port = self._event_object_queue.port

    if error_queue_is_zeromq:
      self._parse_error_queue.name = u'Storage writer error'
      self._parse_error_queue.Open()
      self._parse_error_queue_port = self._parse_error_queue.port

    try:
      self._storage_writer.WriteEventObjects()
      while (event_queue_is_zeromq and
             not self._extraction_complete_event.is_set()):
        logging.debug(u'Storage writer event queue stalled. Restarting and '
                      u'waiting for extraction to complete.')
        self._storage_writer.WriteEventObjects()
    except Exception as exception:
      logging.warning(
          u'Unhandled exception in storage writer (PID: {0:d}).'.format(
              self._pid))
      logging.exception(exception)

    self._event_object_queue.Close()
    self._parse_error_queue.Close()

    logging.debug(u'Storage writer (PID: {0:d}) stopped.'.format(self._pid))

  def SignalAbort(self):
    """Signals the process to abort."""
    self._storage_writer.SignalAbort()


class MultiProcessingQueue(queue.Queue):
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
