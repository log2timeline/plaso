# -*- coding: utf-8 -*-
"""This file contains a foreman class for monitoring processes."""

import collections
import logging

from plaso.engine import processing_status
from plaso.lib import definitions
from plaso.multi_processing import process_info
from plaso.multi_processing import rpc
from plaso.multi_processing import xmlrpc


class Foreman(object):
  """A foreman class that monitors processes.

  The foreman is responsible for monitoring processes and reporting status
  information.

  The worker status information contains among other things:
  * the number of events extracted by each worker;
  * the path specification of the current file entry the worker is processing;
  * an indicator whether the worker is alive or not;
  * the memory consumption of the worker.

  This information is gathered using both RPC calls to the processes
  as well as data provided by the psutil library.

  In the future the Foreman should be able to actively monitor
  the health of the processes and terminate and restart processes
  that are stuck.
  """

  # TODO: refactor process label, instead keep a list of processes and
  # process information objects.
  PROCESS_LABEL = collections.namedtuple(
      u'process_label', u'label pid process_information')

  def __init__(self, event_queue_producer, show_memory_usage=False):
    """Initialize the foreman process.

    Args:
      event_queue_producer: The event object queue producer (instance of
                            ItemQueueProducer).
      show_memory_usage: Optional boolean value to indicate memory information
                         should be included in logging. The default is false.
    """
    super(Foreman, self).__init__()
    self._event_queue_producer = event_queue_producer
    self._monitored_process_labels = {}
    self._processes_per_pid = {}
    self._rpc_clients_per_pid = {}
    self._show_memory_usage = show_memory_usage

    self.processing_status = processing_status.ProcessingStatus()

  def _CheckStatus(self, process_label):
    """Check status for a single process from the monitoring list.

    This function takes a process label and checks if the corresponding
    process is alive and to collect its status information.

    Args:
      process_label: A process label (instance of PROCESS_LABEL).

    Raises:
      KeyError: if the process label is not in the monitoring list.
      ValueError: if the process label is missing.
    """
    if not process_label:
      raise ValueError(u'Missing process label.')

    if process_label.pid not in self._monitored_process_labels:
      raise KeyError(u'Process label not in monitoring list.')

    process_is_alive = process_label.process_information.IsAlive()
    if process_is_alive:
      rpc_client = self._rpc_clients_per_pid.get(process_label.pid, None)
      process_status = rpc_client.CallFunction()
    else:
      process_status = None

    status_indicator = None
    if process_status and isinstance(process_status, dict):
      self._UpdateProcessingStatus(process_label, process_status)
      if self._show_memory_usage:
        self._LogMemoryUsage(process_label)

      status_indicator = process_status.get(u'processing_status', None)

    elif process_status:
      logging.warning((
          u'Unable to retrieve process: {0:s} status via RPC socket: '
          u'http://localhost:{1:d}').format(
              process_label.label, process_label.pid))

    if not process_is_alive:
      logging.warning(u'Process {0:s} (PID: {1:d}) is not alive.'.format(
          process_label.label, process_label.pid))

      self._TerminateProcess(process_label)

    elif status_indicator not in [
        definitions.PROCESSING_STATUS_COMPLETED,
        definitions.PROCESSING_STATUS_INITIALIZED,
        definitions.PROCESSING_STATUS_RUNNING]:

      # We need to terminate the process.
      # TODO: Add a function to start a new instance of a process instead of
      # just removing and killing it.
      logging.error((
          u'Process {0:s} (PID: {1:d}) is not functioning when it should be. '
          u'Terminating it and removing from list.').format(
              process_label.label, process_label.pid))

      self._TerminateProcess(process_label)

    elif status_indicator == definitions.PROCESSING_STATUS_COMPLETED:
      logging.info((
          u'Process {0:s} (PID: {1:d}) has completed its processing. '
          u'Total of {2:d} events extracted').format(
              process_label.label, process_label.pid,
              process_status.get(u'number_of_events', 0)))

      self.StopProcessMonitoring(process_label.pid)

  def _LogMemoryUsage(self, process_label):
    """Logs memory information gathered from a process.

    This function will take a process label and call the logging infrastructure
    to log information about the process's memory information.

    Args:
      process_label: A process label (instance of PROCESS_LABEL).
    """
    mem_info = process_label.process_information.GetMemoryInformation()
    logging.info((
        u'{0:s} - RSS: {1:d}, VMS: {2:d}, Shared: {3:d}, Text: {4:d}, lib: '
        u'{5:d}, data: {6:d}, dirty: {7:d}, Memory Percent: {8:0.2f}%').format(
            process_label.label, mem_info.rss, mem_info.vms, mem_info.shared,
            mem_info.text, mem_info.lib, mem_info.data, mem_info.dirty,
            mem_info.percent * 100))

  def _TerminateProcess(self, process_label):
    """Terminate a process in the monitoring list.

    Args:
      process_label: A process label (instance of PROCESS_LABEL).

    Raises:
      KeyError: if the process label is not in the monitoring list.
      ValueError: if the process label is missing.
    """
    if not process_label:
      raise ValueError(u'Missing process label.')

    if process_label.pid not in self._monitored_process_labels:
      raise KeyError(u'Process label not in monitoring list.')

    process_label.process_information.TerminateProcess()

    # Double check the process is dead.
    if process_label.process_information.IsAlive():
      logging.warning(u'Process {0:s} (PID: {1:d}) is still alive.'.format(
          process_label.label, process_label.pid))

    else:
      logging.warning(u'Process {0:s} (PID: {1:d}) status: {2!s}.'.format(
          process_label.label, process_label.pid,
          process_label.process_information.status))

      self.StopProcessMonitoring(process_label.pid)

  def _UpdateProcessingStatus(self, process_label, process_status):
    """Updates the processing status.

    Args:
      process_label: A process label (instance of PROCESS_LABEL).
      process_status: A process status dictionary.
    """
    if not process_status:
      return

    process_type = process_status.get(u'type', None)
    status_indicator = process_status.get(u'processing_status', None)

    if process_type == u'collector':
      number_of_path_specs = process_status.get(u'number_of_path_specs', None)

      self.processing_status.UpdateCollectorStatus(
          process_label.label, process_label.pid, number_of_path_specs,
          status_indicator)

    elif process_type == u'storage_writer':
      number_of_events = process_status.get(u'number_of_events', 0)

      self.processing_status.UpdateStorageWriterStatus(number_of_events)

    elif process_type == u'worker':
      number_of_events = process_status.get(u'number_of_events', 0)
      number_of_path_specs = process_status.get(u'number_of_path_specs', 0)
      display_name = process_status.get(u'display_name', u'')

      self.processing_status.UpdateExtractionWorkerStatus(
          process_label.label, process_label.pid, display_name,
          number_of_events, number_of_path_specs, status_indicator,
          process_label.process_information.status)

  def CheckStatus(self):
    """Checks status of either a single process or all from the monitoring list.

    Returns:
      A boolean indicating whether processing is complete.
    """
    for process_label in self._monitored_process_labels.values():
      self._CheckStatus(process_label)

    processing_completed = self.processing_status.GetProcessingCompleted()
    if processing_completed:
      logging.debug(u'Processing completed.')

    elif self.processing_status.WorkersIdle():
      logging.warning(u'Workers are idle.')
      # TODO: raise an abort exception.

    return processing_completed

  def GetLabelByPid(self, pid):
    """Retrieves a proces label for a specific PID.

    Args:
      pid: The process ID (PID).

    Returns:
      A process label (instance of PROCESS_LABEL) or None.
    """
    return self._monitored_process_labels.get(pid, None)

  def StartProcessMonitoring(self, process):
    """Starts monitoring a processes by adding it to the monitor list.

    Args:
      process: The process object (instance of MultiProcessBaseProcess).

    Raises:
      IOError: if the RPC client cannot connect to the server.
      KeyError: if the process or RPC client is already set for a certain PID.
      ValueError: if the process object is missing.
    """
    if process is None:
      raise ValueError(u'Missing process object.')

    if process.pid in self._processes_per_pid:
      raise KeyError(
          u'Already monitoring process: {0!s} (PID: {1:d})'.format(
              process.name, process.pid))

    if process.pid in self._rpc_clients_per_pid:
      raise KeyError(
          u'RPC client (PID: {0:d}) already exists'.format(process.pid))

    rpc_client = xmlrpc.XMLProcessStatusRPCClient()

    hostname = u'localhost'
    port = rpc.GetProxyPortNumberFromPID(process.pid)
    if not rpc_client.Open(hostname, port):
      raise IOError((
          u'RPC client (PID: {0:d}) unable to connect to server: '
          u'{1:s}:{2:d}').format(process.pid, hostname, port))

    self._processes_per_pid[process.pid] = process
    self._rpc_clients_per_pid[process.pid] = rpc_client

    # TODO: refactor to use process instead of process label.
    process_information = process_info.ProcessInfo(process.pid)
    label = self.PROCESS_LABEL(process.name, process.pid, process_information)

    if label.pid not in self._monitored_process_labels:
      self._monitored_process_labels[label.pid] = label

  def StopProcessMonitoring(self, pid):
    """Stops monitoring a process.

    Args:
      pid: The process identifier.

    Raises:
      KeyError: if the process PID is not being monitored.
    """
    if pid not in self._processes_per_pid:
      raise KeyError(u'Not monitoring process (PID: {0:d})'.format(pid))

    if pid not in self._monitored_process_labels:
      raise KeyError(
          u'Process (PID: {0:d}) not in monitoring list.'.format(pid))

    del self._processes_per_pid[pid]

    process_label = self._monitored_process_labels[pid]
    del self._monitored_process_labels[pid]

    # Remove the RPC client.
    rpc_client = self._rpc_clients_per_pid.get(pid, None)
    if rpc_client:
      rpc_client.Close()
      del self._rpc_clients_per_pid[pid]

    logging.info((
        u'Process: {0:s} (PID: {1:d}) has been removed from the monitored '
        u'list.').format(process_label.label, pid))
