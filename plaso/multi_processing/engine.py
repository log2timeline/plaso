# -*- coding: utf-8 -*-
"""The multi-process processing engine."""

import abc
import ctypes
import logging
import os
import signal
import sys
import threading
import time

from plaso.engine import engine
from plaso.lib import definitions
from plaso.multi_processing import process_info
from plaso.multi_processing import plaso_xmlrpc


class MultiProcessEngine(engine.BaseEngine):
  """Class that defines the base multi-process engine.

  This class contains functionality to:
  * monitor and manage worker processes;
  * retrieve a process status information via RPC;
  * manage the status update thread.
  """

  # Note that on average Windows seems to require a longer wait.
  _RPC_SERVER_TIMEOUT = 8.0
  _MAXIMUM_RPC_ERRORS = 10

  _ZEROMQ_NO_WORKER_REQUEST_TIME_SECONDS = 300

  def __init__(
      self, debug_output=False, enable_profiling=False,
      profiling_directory=None, profiling_sample_rate=1000,
      profiling_type=u'all'):
    """Initializes an engine object.

    Args:
      debug_output (Optional[bool]): True if debug output should be enabled.
      enable_profiling (Optional[bool]): True if profiling should be enabled.
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
    """
    super(MultiProcessEngine, self).__init__(
        debug_output=debug_output, enable_profiling=enable_profiling,
        profiling_directory=profiling_directory,
        profiling_sample_rate=profiling_sample_rate,
        profiling_type=profiling_type)
    self._name = u'Main'
    self._pid = os.getpid()
    self._process_information_per_pid = {}
    self._processes_per_pid = {}
    self._rpc_clients_per_pid = {}
    self._rpc_errors_per_pid = {}
    self._show_memory_usage = False
    self._status_update_active = False
    self._status_update_callback = None
    self._status_update_thread = None

  def _AbortJoin(self, timeout=None):
    """Aborts all registered processes by joining with the parent process.

    Args:
      timeout (int): number of seconds to wait for processes to join, where
          None represents no timeout.
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
          u'processing_status': processing_status_string}

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

  # TODO: refactor this function.
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
    rpc_client = plaso_xmlrpc.XMLProcessStatusRPCClient()

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

  def _StartStatusUpdateThread(self):
    """Starts the status update thread."""
    self._status_update_active = True
    self._status_update_thread = threading.Thread(
        name=u'Status update', target=self._StatusUpdateThreadMain)
    self._status_update_thread.start()

  @abc.abstractmethod
  def _StatusUpdateThreadMain(self):
    """Main function of the status update thread."""

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

  def _StopMonitoringProcesses(self):
    """Stops monitoring all processes."""
    for pid in iter(self._process_information_per_pid.keys()):
      self._StopMonitoringProcess(pid)

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
