# -*- coding: utf-8 -*-
"""This file contains a foreman class for monitoring processes."""

import ctypes
import logging
import os
import signal
import sys

from plaso.engine import processing_status
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import process_info
from plaso.multi_processing import rpc
from plaso.multi_processing import xmlrpc


class Foreman(object):
  """A foreman class that monitors the extraction of events.

  The foreman is responsible for monitoring processes and queues.
  The foreman gathers process information using both RPC calls to
  the processes as well as data provided by the psutil library.

  The foreman monitors among other things:
  * the path specification of the current file entry the worker is processing;
  * the number of events extracted by each worker;
  * an indicator whether a process is alive or not;
  * the memory consumption of the processes.

  Attributes:
    error_detected: boolean value to indicate whether the foreman
                    detected an error.
    processing_status: the processing status object (instance of
                       ProcessingStatus).
  """

  def __init__(
      self, path_spec_queue, event_object_queue, parse_error_queue,
      show_memory_usage=False):
    """Initialize the foreman process.

    Args:
      path_spec_queue: the path specification queue object (instance of
                       MultiProcessingQueue).
      event_object_queue: the event object queue object (instance of
                          MultiProcessingQueue).
      parse_error_queue: the parser error queue object (instance of
                         MultiProcessingQueue).
      show_memory_usage: Optional boolean value to indicate memory information
                         should be included in logging. The default is false.
    """
    super(Foreman, self).__init__()
    self._error_path_specs = []
    self._event_object_queue = event_object_queue
    self._parse_error_queue = parse_error_queue
    self._path_spec_queue = path_spec_queue
    self._process_information_per_pid = {}
    self._processes_per_pid = {}
    self._rpc_clients_per_pid = {}
    self._rpc_errors_per_pid = {}
    self._show_memory_usage = show_memory_usage

    self.error_detected = False
    self.processing_status = processing_status.ProcessingStatus()

  def _CheckStatus(self, pid):
    """Check status for a single process from the monitoring list.

    Args:
      pid: The process ID (PID).

    Raises:
      ForemanAbort: when the collector or storage worker process
                    unexpectedly terminated.
      KeyError: if the process is not registered with the foreman.
    """
    self._RaiseIfNotRegistered(pid)

    process = self._processes_per_pid[pid]

    process_is_alive = process.is_alive()
    if process_is_alive:
      rpc_client = self._rpc_clients_per_pid.get(pid, None)
      process_status = rpc_client.CallFunction()
    else:
      process_status = None

    if isinstance(process_status, dict):
      self._rpc_errors_per_pid[pid] = 0

      status_indicator = process_status.get(u'processing_status', None)

    else:
      rpc_errors = self._rpc_errors_per_pid.get(pid, 0) + 1
      self._rpc_errors_per_pid[pid] = rpc_errors

      if rpc_errors > 10:
        process_is_alive = False

      if process_is_alive:
        logging.warning((
            u'Unable to retrieve process: {0:s} status via RPC socket: '
            u'http://localhost:{1:d}').format(process.name, pid))

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
        self._error_path_specs.append(path_spec)

    self._UpdateProcessingStatus(pid, process_status)

    if status_indicator not in [
        definitions.PROCESSING_STATUS_COMPLETED,
        definitions.PROCESSING_STATUS_INITIALIZED,
        definitions.PROCESSING_STATUS_RUNNING]:

      logging.error(
          u'Process {0:s} (PID: {1:d}) is not functioning correctly.'.format(
              process.name, pid))

      self.error_detected = True

      if process.type == definitions.PROCESS_TYPE_COLLECTOR:
        raise errors.ForemanAbort(u'Collector unexpectedly terminated')

      if process.type == definitions.PROCESS_TYPE_STORAGE_WRITER:
        raise errors.ForemanAbort(u'Storage writer unexpectedly terminated')

      # We need to terminate the process.
      # TODO: Add a function to start a new instance of a process instead of
      # just removing and killing it.
      self._TerminateProcess(pid)

    elif status_indicator == definitions.PROCESSING_STATUS_COMPLETED:
      logging.debug((
          u'Process {0:s} (PID: {1:d}) has completed its processing. '
          u'Total of {2:d} events extracted').format(
              process.name, pid, process_status.get(u'number_of_events', 0)))

      self._StopMonitoringProcess(pid)

    elif self._show_memory_usage:
      self._LogMemoryUsage(pid)

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
      KeyError: if the process is not registered with the foreman.
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

  def _StartMonitoringProcess(self, pid):
    """Starts monitoring a process.

    Args:
      pid: The process identifier.

    Raises:
      KeyError: if the process is not registered with the foreman or
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

    rpc_client = xmlrpc.XMLProcessStatusRPCClient()

    hostname = u'localhost'
    port = rpc.GetProxyPortNumberFromPID(pid)
    if not rpc_client.Open(hostname, port):
      raise IOError((
          u'RPC client (PID: {0:d}) unable to connect to server: '
          u'{1:s}:{2:d}').format(pid, hostname, port))

    self._rpc_clients_per_pid[pid] = rpc_client
    self._process_information_per_pid[pid] = process_info.ProcessInfo(pid)

  def _RaiseIfNotMonitored(self, pid):
    """Raises if the process is not monitored by the foreman.

    Args:
      pid: The process identifier.

    Raises:
      KeyError: if the process is not monitored by the foreman.
    """
    if pid not in self._process_information_per_pid:
      raise KeyError(
          u'Process (PID: {0:d}) not monitored by foreman.'.format(pid))

  def _RaiseIfNotRegistered(self, pid):
    """Raises if the process is not registered with the foreman.

    Args:
      pid: The process identifier.

    Raises:
      KeyError: if the process is not registered with the foreman.
    """
    if pid not in self._processes_per_pid:
      raise KeyError(
          u'Process (PID: {0:d}) not registered with foreman'.format(pid))

  def _StopMonitoringProcess(self, pid):
    """Stops monitoring a process.

    Args:
      pid: The process identifier.

    Raises:
      KeyError: if the process is not registered with the foreman or
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

  def _TerminateProcess(self, pid):
    """Terminate a process.

    Args:
      pid: The process identifier.

    Raises:
      KeyError: if the process is not registered with the foreman.
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
      KeyError: if the process is not registered with the foreman.
    """
    self._RaiseIfNotRegistered(pid)

    if not process_status:
      return

    process = self._processes_per_pid[pid]

    process_type = process_status.get(u'type', None)
    status_indicator = process_status.get(u'processing_status', None)

    if process_type == definitions.PROCESS_TYPE_COLLECTOR:
      number_of_path_specs = process_status.get(u'number_of_path_specs', None)

      self.processing_status.UpdateCollectorStatus(
          process.name, pid, number_of_path_specs, status_indicator)

    elif process_type == definitions.PROCESS_TYPE_STORAGE_WRITER:
      number_of_events = process_status.get(u'number_of_events', 0)

      self.processing_status.UpdateStorageWriterStatus(
          process.name, pid, number_of_events, status_indicator)

    elif process_type == definitions.PROCESS_TYPE_WORKER:
      self._RaiseIfNotMonitored(pid)

      number_of_events = process_status.get(u'number_of_events', 0)
      number_of_path_specs = process_status.get(u'number_of_path_specs', 0)
      display_name = process_status.get(u'display_name', u'')
      process_information = self._process_information_per_pid[pid]

      self.processing_status.UpdateExtractionWorkerStatus(
          process.name, pid, display_name, number_of_events,
          number_of_path_specs, status_indicator, process_information.status)

  def AbortJoin(self, timeout=None):
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

  def AbortKill(self):
    """Aborts all registered processes by sending a SIGKILL or equivalent."""
    for pid, process in iter(self._processes_per_pid.items()):
      if not process.is_alive():
        continue

      logging.warning(u'Killing process: {0:s} (PID: {1:d}).'.format(
          process.name, pid))
      self._KillProcess(pid)

  def AbortTerminate(self):
    """Aborts all registered processes by sending a SIGTERM or equivalent."""
    for pid, process in iter(self._processes_per_pid.items()):
      if not process.is_alive():
        continue

      logging.warning(u'Terminating process: {0:s} (PID: {1:d}).'.format(
          process.name, pid))
      process.terminate()

  def CheckStatus(self):
    """Checks status of the monitored processes.

    Returns:
      A boolean indicating whether processing is complete.

    Raises:
      ForemanAbort: when all the worker are idle.
    """
    for pid in iter(self._process_information_per_pid.keys()):
      self._CheckStatus(pid)

    processing_completed = self.processing_status.GetProcessingCompleted()
    if processing_completed:
      if not self.error_detected:
        logging.debug(u'Processing completed.')

    elif self.processing_status.WorkersIdle():
      logging.error(u'Workers idle for too long')
      self.error_detected = True
      raise errors.ForemanAbort(u'Workers idle for too long')

    return processing_completed

  def RegisterProcess(self, process):
    """Registers a process to be registered with the foreman.

    Args:
      process: The process object (instance of MultiProcessBaseProcess).

    Raises:
      KeyError: if the process is already registered with the foreman.
      ValueError: if the process object is missing.
    """
    if process is None:
      raise ValueError(u'Missing process object.')

    if process.pid in self._processes_per_pid:
      raise KeyError(
          u'Already managing process: {0!s} (PID: {1:d})'.format(
              process.name, process.pid))

    self._processes_per_pid[process.pid] = process

  def StartProcessMonitoring(self):
    """Starts monitoring the registered processes."""
    for pid in iter(self._processes_per_pid.keys()):
      self._StartMonitoringProcess(pid)

  def StopProcessMonitoring(self):
    """Stops monitoring processes."""
    for pid in iter(self._process_information_per_pid.keys()):
      self._StopMonitoringProcess(pid)
