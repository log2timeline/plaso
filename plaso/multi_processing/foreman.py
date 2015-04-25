# -*- coding: utf-8 -*-
"""This file contains a foreman class for monitoring workers."""

import collections
import logging

from plaso.multi_processing import process_info
from plaso.multi_processing import rpc
from plaso.multi_processing import xmlrpc


class Foreman(object):
  """A foreman class that monitors workers.

  The Foreman is responsible for monitoring worker processes
  and give back status information. The status information contains
  among other things:
  * the number of events extracted by each worker;
  * the path specification of the current file entry the worker is processing;
  * an indicator whether the worker is alive or not;
  * the memory consumption of the worker.

  This information is gathered using both RPC calls to the worker
  itself as well as data provided by the psutil library.

  In the future the Foreman should be able to actively monitor
  the health of the processes and terminate and restart processes
  that are stuck.
  """

  PROCESS_LABEL = collections.namedtuple(u'process_label', u'label pid process')

  def __init__(self, event_queue_producer, show_memory_usage=False):
    """Initialize the foreman process.

    Args:
      event_queue_producer: The event object queue producer (instance of
                            ItemQueueProducer).
      show_memory_usage: Optional boolean value to indicate memory information
                         should be included in logging. The default is false.
    """
    super(Foreman, self).__init__()
    self._completed_process_labels = {}
    self._event_queue_producer = event_queue_producer
    self._last_status_dict = {}
    self._monitored_process_labels = {}
    self._processing_completed = False
    self._rpc_clients_per_pid = {}
    self._show_memory_usage = show_memory_usage
    self._signalled_end_of_input = False

  def _CheckStatus(self, process_label):
    """Check status for a single process from the monitoring list.

    This function will take a single label, which describes a worker process
    and check if it is alive, call the appropriate functions to log down
    information extracted from the worker and if a process is no longer alive
    and processing has been marked as done, it will remove the worker from
    the list of monitored workers. This function is also reponsible for killing
    or terminating a process that is alive and hanging, or not alive while
    it should be alive.

    In the future this function will also be responsible for restarting
    a worker, or signalling the engine that it needs to spin up a new worker
    in the case of a worker dying or being in an effective zombie state.

    Args:
      process_label: A process label (instance of PROCESS_LABEL).

    Returns:
      A boolean indicating whether processing is complete.

    Raises:
      KeyError: if the process label is not in the monitoring list.
      ValueError: if the process label is missing.
    """
    if not process_label:
      raise ValueError(u'Missing process label.')

    if process_label.pid not in self._monitored_process_labels:
      raise KeyError(u'Process label not in monitoring list.')

    worker_is_running = True
    if not process_label.process.IsAlive():
      logging.info(u'Process {0:s} (PID: {1:d}) is not alive.'.format(
          process_label.label, process_label.pid))

    else:
      rpc_client = self._rpc_clients_per_pid.get(process_label.pid, None)
      status_dict = rpc_client.CallFunction()
      if not isinstance(status_dict, dict):
        logging.warning((
            u'Unable to retrieve status of process: {0:s} via RPC socket: '
            u'http://localhost:{1:d}').format(
                process_label.label, process_label.pid))

      else:
        self._last_status_dict[process_label.pid] = status_dict
        worker_is_running = status_dict.get(u'is_running', False)
        if worker_is_running:
          self._LogWorkerInformation(process_label, status_dict)
          if self._show_memory_usage:
            self._LogMemoryUsage(process_label)
          return False

        logging.info((
            u'Process {0:s} (PID: {1:d}) has completed its processing. '
            u'Total of {2:d} events extracted').format(
                process_label.label, process_label.pid,
                status_dict.get(u'number_of_events', 0)))

    if worker_is_running and not self._processing_completed:
      # We need to terminate the process.
      # TODO: Add a function to start a new instance of a worker instead of
      # just removing and killing it.
      logging.error((
          u'Process {0:s} (PID: {1:d}) is not functioning when it should be. '
          u'Terminating it and removing from list.').format(
              process_label.label, process_label.pid))

      self._TerminateProcess(process_label)
      return False

    # This process exited properly and should have. Let's remove it from our
    # list of labels.
    self.StopMonitoring(process_label)

    # Add the process label to the completed list and remove the RPC client.
    self._completed_process_labels[process_label.pid] = process_label
    rpc_client = self._rpc_clients_per_pid.get(process_label.pid, None)
    if rpc_client:
      rpc_client.Close()
      del self._rpc_clients_per_pid[process_label.pid]

    return True

  def _LogMemoryUsage(self, process_label):
    """Logs memory information gathered from a process.

    This function will take a process label and call the logging infrastructure
    to log information about the process's memory information.

    Args:
      process_label: A process label (instance of PROCESS_LABEL).
    """
    mem_info = process_label.process.GetMemoryInformation()
    logging.info((
        u'{0:s} - RSS: {1:d}, VMS: {2:d}, Shared: {3:d}, Text: {4:d}, lib: '
        u'{5:d}, data: {6:d}, dirty: {7:d}, Memory Percent: {8:0.2f}%').format(
            process_label.label, mem_info.rss, mem_info.vms, mem_info.shared,
            mem_info.text, mem_info.lib, mem_info.data, mem_info.dirty,
            mem_info.percent * 100))

  def _LogWorkerInformation(self, process_label, status=None):
    """Log information gathered from the worker.

    Args:
      process_label: A process label (instance of PROCESS_LABEL).
      status: Optional worker status dictonary. The default is None.
    """
    if status:
      # TODO: change file to "display name".
      logging.info((
          u'{0:s} (PID: {1:d}) - events extracted: {2:d} - file: {3:s} '
          u'- running: {4!s} <{5:s}>').format(
              process_label.label, process_label.pid,
              status.get(u'number_of_events', -1),
              status.get(u'current_file', u''),
              status.get(u'is_running', False), process_label.process.status))

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

    process_label.process.TerminateProcess()

    # Double check the process is dead.
    if process_label.process.IsAlive():
      logging.warning(u'Process {0:s} (PID: {1:d}) is still alive.'.format(
          process_label.label, process_label.pid))

    else:
      logging.warning(u'Process {0:s} (PID: {1:d}) status: {2!s}.'.format(
          process_label.label, process_label.pid, process_label.process.status))

      self.StopMonitoring(process_label)

  def CheckStatus(self, process_label=None):
    """Checks status of either a single process or all from the monitoring list.

    Args:
      process_label: Optional process label (instance of PROCESS_LABEL).
                     The default is None with represents the status of all
                     monitored processes should be checked.

    Returns:
      A boolean indicating whether processing is complete.
    """
    if process_label is not None:
      return self._CheckStatus(process_label)

    # Note that self._monitored_process_labels can be altered in this loop
    # hence we need it to be sorted.
    processing_complete = True
    if self._signalled_end_of_input:
      logging.info(u'Waiting for storage.')
    else:
      for _, process_label in sorted(self._monitored_process_labels.items()):
        if not self._CheckStatus(process_label):
          processing_complete = False

    if not self._processing_completed:
      if processing_complete and not self._signalled_end_of_input:
        logging.info(u'All extraction workers stopped.')
        self._event_queue_producer.SignalEndOfInput()
        self._signalled_end_of_input = True
      return False

    if self._processing_completed and processing_complete:
      logging.info(u'Processing completed.')
    return processing_complete

  def GetLabelByPid(self, pid):
    """Retrieves a proces label for a specific PID.

    Args:
      pid: The process ID (PID).

    Returns:
      A process label (instance of PROCESS_LABEL) or None.
    """
    process_label = self._monitored_process_labels.get(pid, None)
    if not process_label:
      process_label = self._completed_process_labels.get(pid, None)
    return process_label

  def HasCompleted(self, process_label):
    """Determines if a worker process has completed.

    Args:
      process_label: A process label (instance of PROCESS_LABEL).
    """
    return process_label.pid in self._completed_process_labels

  def IsMonitored(self, process_label):
    """Determines if a worker process is being monitored.

    Args:
      process_label: A process label (instance of PROCESS_LABEL).
    """
    return process_label.pid in self._monitored_process_labels

  def MonitorWorker(self, label=None, pid=None, name=None):
    """Starts monitoring a worker by adding it to the monitor list.

    This function requires either a label to be set or a PID and a process
    name. If the label is empty or if both a PID and a name is not provided
    the function does nothing, as in no process is added to the list of
    workers to monitor (and no indication).

    Args:
      label: A process label (instance of PROCESS_LABEL), if not provided
             then a pid and a name is required. Defaults to None (if None
             then both a pid and name have to be provided).
      pid: The process ID (PID) of the worker that should be added to the
           monitor list. This is only required if label is not provided.
           Defaults to None. This is only used if label is set to None, in
           which case it has to be set.
      name: The name of the worker process, only required if label is not
            provided. Defaults to None, only used if label is set to None,
            in which case it has to be set.

    Raises:
      IOError: if the RPC client cannot connect to the server.
      RuntimeError: if the RPC client is already set for a certain PID.
    """
    if label is None:
      if pid is None or name is None:
        return

      if pid in self._rpc_clients_per_pid:
        raise RuntimeError(
            u'RPC client (PID: {0:d}) already exists'.format(pid))

      rpc_client = xmlrpc.XMLProcessStatusRPCClient()

      hostname = u'localhost'
      port = rpc.GetProxyPortNumberFromPID(pid)
      if not rpc_client.Open(hostname, port):
        raise IOError((
            u'RPC client (PID: {0:d}) unable to connect to server: '
            u'{1:s}:{2:d}').format(pid, hostname, port))

      self._rpc_clients_per_pid[pid] = rpc_client

      process_information = process_info.ProcessInfo(pid)
      label = self.PROCESS_LABEL(name, pid, process_information)

    if label.pid not in self._monitored_process_labels:
      if label.pid in self._completed_process_labels:
        del self._completed_process_labels[label.pid]
      self._monitored_process_labels[label.pid] = label

  def SignalEndOfProcessing(self):
    """Signals that the processing is completed."""
    self._processing_completed = True

    logging.info(
        u'Foreman received a signal indicating that processing is completed.')

    # This function may be called via RPC functions that expect a value
    # to be returned.
    return True

  def StopMonitoring(self, process_label):
    """Stops monitoring a worker process.

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

    del self._monitored_process_labels[process_label.pid]

    logging.info((
        u'Worker: {0:s} (PID: {1:d}) has been removed from the monitored '
        u'list.').format(process_label.label, process_label.pid))
