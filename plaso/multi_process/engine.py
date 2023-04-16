# -*- coding: utf-8 -*-
"""The multi-process processing engine."""

import abc
import ctypes
import os
import signal
import sys
import threading
import time

from plaso.engine import engine
from plaso.engine import process_info
from plaso.lib import definitions
from plaso.multi_process import logger
from plaso.multi_process import plaso_xmlrpc


class MultiProcessEngine(engine.BaseEngine):
  """Multi-process engine base.

  This class contains functionality to:
  * monitor and manage worker processes;
  * retrieve a process status information via RPC;
  * manage the status update thread.
  """

  # Note that on average Windows seems to require a longer wait.
  _RPC_SERVER_TIMEOUT = 8.0
  _MAXIMUM_RPC_ERRORS = 10
  # Maximum number of attempts to try to start a replacement worker process.
  _MAXIMUM_REPLACEMENT_RETRIES = 3
  # Number of seconds to wait between attempts to start a replacement worker
  # process
  _REPLACEMENT_WORKER_RETRY_DELAY = 1

  _PROCESS_JOIN_TIMEOUT = 5.0

  _ZEROMQ_NO_WORKER_REQUEST_TIME_SECONDS = 300

  def __init__(self):
    """Initializes a multi-process engine."""
    super(MultiProcessEngine, self).__init__()
    self._debug_output = False
    self._name = 'Main'
    self._last_worker_number = 0
    self._log_filename = None
    self._pid = os.getpid()
    self._process_information = process_info.ProcessInfo(self._pid)
    self._process_information_per_pid = {}
    self._processes_per_pid = {}
    self._quiet_mode = False
    self._rpc_clients_per_pid = {}
    self._rpc_errors_per_pid = {}
    self._status_update_active = False
    self._status_update_thread = None
    self._storage_writer = None
    self._worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT

  def _AbortJoin(self, timeout=None):
    """Aborts all registered processes by joining with the parent process.

    Args:
      timeout (int): number of seconds to wait for processes to join, where
          None represents no timeout.
    """
    for pid, process in self._processes_per_pid.items():
      logger.debug('Waiting for process: {0:s} (PID: {1:d}).'.format(
          process.name, pid))
      process.join(timeout=timeout)
      if not process.is_alive():
        logger.debug('Process {0:s} (PID: {1:d}) stopped.'.format(
            process.name, pid))

  def _AbortKill(self):
    """Aborts all registered processes by sending a SIGKILL or equivalent."""
    for pid, process in self._processes_per_pid.items():
      if not process.is_alive():
        continue

      logger.warning('Killing process: {0:s} (PID: {1:d}).'.format(
          process.name, pid))
      self._KillProcess(pid)

  def _AbortTerminate(self):
    """Aborts all registered processes by sending a SIGTERM or equivalent."""
    for pid, process in self._processes_per_pid.items():
      if not process.is_alive():
        continue

      logger.warning('Terminating process: {0:s} (PID: {1:d}).'.format(
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

    process_status = self._QueryProcessStatus(process)
    if process_status is None:
      process_is_alive = False
    else:
      process_is_alive = True

    process_information = self._process_information_per_pid[pid]
    used_memory = process_information.GetUsedMemory() or 0

    if self._worker_memory_limit and used_memory > self._worker_memory_limit:
      logger.warning((
          'Process: {0:s} (PID: {1:d}) killed because it exceeded the '
          'memory limit: {2:d}.').format(
              process.name, pid, self._worker_memory_limit))
      self._KillProcess(pid)

    if isinstance(process_status, dict):
      self._rpc_errors_per_pid[pid] = 0
      status_indicator = process_status.get('processing_status', None)

    else:
      rpc_errors = self._rpc_errors_per_pid.get(pid, 0) + 1
      self._rpc_errors_per_pid[pid] = rpc_errors

      if rpc_errors > self._MAXIMUM_RPC_ERRORS:
        process_is_alive = False

      if process_is_alive:
        rpc_port = process.rpc_port.value
        logger.warning((
            'Unable to retrieve process: {0:s} (PID: {1:d}) status via '
            'RPC socket: http://localhost:{2:d}').format(
                process.name, pid, rpc_port))

        processing_status_string = 'RPC error'
        status_indicator = definitions.STATUS_INDICATOR_RUNNING
      else:
        processing_status_string = 'killed'
        status_indicator = definitions.STATUS_INDICATOR_KILLED

      process_status = {
          'processing_status': processing_status_string}

    self._UpdateProcessingStatus(pid, process_status, used_memory)

    # _UpdateProcessingStatus can also change the status of the worker,
    # So refresh the status if applicable.
    for worker_status in self._processing_status.workers_status:
      if worker_status.pid == pid:
        status_indicator = worker_status.status
        break

    if status_indicator in definitions.ERROR_STATUS_INDICATORS:
      logger.error((
          'Process {0:s} (PID: {1:d}) is not functioning correctly. '
          'Status code: {2!s}.').format(process.name, pid, status_indicator))

      self._TerminateProcessByPid(pid)

      replacement_process = None
      replacement_process_name = 'Worker_{0:02d}'.format(
          self._last_worker_number)
      for replacement_process_attempt in range(
          self._MAXIMUM_REPLACEMENT_RETRIES):
        logger.info((
            'Attempt: {0:d} to start replacement worker process for '
            '{1:s}').format(replacement_process_attempt + 1, process.name))

        replacement_process = self._StartWorkerProcess(replacement_process_name)
        if replacement_process:
          break

        time.sleep(self._REPLACEMENT_WORKER_RETRY_DELAY)

      if not replacement_process:
        logger.error(
            'Unable to create replacement worker process for: {0:s}'.format(
                process.name))

  def _KillProcess(self, pid):
    """Issues a SIGKILL or equivalent to the process.

    Args:
      pid (int): process identifier (PID).
    """
    if sys.platform.startswith('win'):
      process_terminate = 1
      handle = ctypes.windll.kernel32.OpenProcess(
          process_terminate, False, pid)
      ctypes.windll.kernel32.TerminateProcess(handle, -1)
      ctypes.windll.kernel32.CloseHandle(handle)

    else:
      try:
        os.kill(pid, signal.SIGKILL)
      except OSError as exception:
        logger.error('Unable to kill process {0:d} with error: {1!s}'.format(
            pid, exception))

  def _QueryProcessStatus(self, process):
    """Queries a process to determine its status.

    Args:
      process (MultiProcessBaseProcess): process to query for its status.

    Returns:
      dict[str, str]: status values received from the worker process.
    """
    process_is_alive = process.is_alive()
    if not process_is_alive:
      return None

    rpc_client = self._rpc_clients_per_pid.get(process.pid, None)
    return rpc_client.CallFunction()

  def _RaiseIfNotMonitored(self, pid):
    """Raises if the process is not monitored by the engine.

    Args:
      pid (int): process identifier (PID).

    Raises:
      KeyError: if the process is not monitored by the engine.
    """
    if pid not in self._process_information_per_pid:
      raise KeyError(
          'Process (PID: {0:d}) not monitored by engine.'.format(pid))

  def _RaiseIfNotRegistered(self, pid):
    """Raises if the process is not registered with the engine.

    Args:
      pid (int): process identifier (PID).

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    if pid not in self._processes_per_pid:
      raise KeyError(
          'Process (PID: {0:d}) not registered with engine'.format(pid))

  def _RegisterProcess(self, process):
    """Registers a process with the engine.

    Args:
      process (MultiProcessBaseProcess): process.

    Raises:
      KeyError: if the process is already registered with the engine.
      ValueError: if the process is missing.
    """
    if process is None:
      raise ValueError('Missing process.')

    if process.pid in self._processes_per_pid:
      raise KeyError(
          'Already managing process: {0!s} (PID: {1:d})'.format(
              process.name, process.pid))

    self._processes_per_pid[process.pid] = process

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def _StartWorkerProcess(self, process_name):
    """Creates, starts, monitors and registers a worker process.

    Args:
      process_name (str): process name.

    Returns:
      MultiProcessWorkerProcess: extraction worker process.
    """

  def _StartMonitoringProcess(self, process):
    """Starts monitoring a process.

    Args:
      process (MultiProcessBaseProcess): process.

    Raises:
      IOError: if the RPC client cannot connect to the server.
      KeyError: if the process is not registered with the engine or
          if the process is already being monitored.
      OSError: if the RPC client cannot connect to the server.
      ValueError: if the process is missing.
    """
    if process is None:
      raise ValueError('Missing process.')

    pid = process.pid

    if pid in self._process_information_per_pid:
      raise KeyError(
          'Already monitoring process (PID: {0:d}).'.format(pid))

    if pid in self._rpc_clients_per_pid:
      raise KeyError(
          'RPC client (PID: {0:d}) already exists'.format(pid))

    rpc_client = plaso_xmlrpc.XMLProcessStatusRPCClient()

    # Make sure that a worker process has started its RPC server.
    # The RPC port will be 0 if no server is available.
    rpc_port = process.rpc_port.value
    time_waited_for_process = 0.0
    while not rpc_port:
      time.sleep(0.1)
      rpc_port = process.rpc_port.value
      time_waited_for_process += 0.1

      if time_waited_for_process >= self._RPC_SERVER_TIMEOUT:
        raise IOError(
            'RPC client unable to determine server (PID: {0:d}) port.'.format(
                pid))

    hostname = 'localhost'

    if not rpc_client.Open(hostname, rpc_port):
      raise IOError((
          'RPC client unable to connect to server (PID: {0:d}) '
          'http://{1:s}:{2:d}').format(pid, hostname, rpc_port))

    self._rpc_clients_per_pid[pid] = rpc_client
    self._process_information_per_pid[pid] = process_info.ProcessInfo(pid)

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
      time.sleep(self._status_update_interval)

  def _StopMonitoringProcess(self, process):
    """Stops monitoring a process.

    Args:
      process (MultiProcessBaseProcess): process.

    Raises:
      KeyError: if the process is not monitored.
      ValueError: if the process is missing.
    """
    if process is None:
      raise ValueError('Missing process.')

    pid = process.pid

    self._RaiseIfNotMonitored(pid)

    del self._process_information_per_pid[pid]

    rpc_client = self._rpc_clients_per_pid.get(pid, None)
    if rpc_client:
      rpc_client.Close()
      del self._rpc_clients_per_pid[pid]

    if pid in self._rpc_errors_per_pid:
      del self._rpc_errors_per_pid[pid]

    logger.debug('Stopped monitoring process: {0:s} (PID: {1:d})'.format(
        process.name, pid))

  def _StopMonitoringProcesses(self):
    """Stops monitoring all processes."""
    # We need to make a copy of the list of pids since we are changing
    # the dict in the loop.
    for pid in list(self._process_information_per_pid.keys()):
      self._RaiseIfNotRegistered(pid)
      process = self._processes_per_pid[pid]

      self._StopMonitoringProcess(process)

  def _StopStatusUpdateThread(self):
    """Stops the status update thread."""
    if self._status_update_thread:
      self._status_update_active = False
      if self._status_update_thread.is_alive():
        self._status_update_thread.join()
      self._status_update_thread = None

    # Update the status view one last time so we have the latest worker process
    # status information.
    self._UpdateStatus()

  def _TerminateProcessByPid(self, pid):
    """Terminate a process that's monitored by the engine.

    Args:
      pid (int): process identifier (PID).

    Raises:
      KeyError: if the process is not registered with and monitored by the
          engine.
    """
    self._RaiseIfNotRegistered(pid)

    process = self._processes_per_pid[pid]

    self._TerminateProcess(process)
    self._StopMonitoringProcess(process)

  def _TerminateProcess(self, process):
    """Terminate a process.

    Args:
      process (MultiProcessBaseProcess): process to terminate.
    """
    pid = process.pid
    logger.warning('Terminating process: (PID: {0:d}).'.format(pid))
    process.terminate()

    # Wait for the process to exit.
    process.join(timeout=self._PROCESS_JOIN_TIMEOUT)

    if process.is_alive():
      logger.warning('Killing process: (PID: {0:d}).'.format(pid))
      self._KillProcess(pid)

  @abc.abstractmethod
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

  @abc.abstractmethod
  def _UpdateStatus(self):
    """Updates the status."""
