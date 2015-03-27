# -*- coding: utf-8 -*-
"""This file contains a foreman class for monitoring workers."""

import collections
import logging

from plaso.multi_processing import process_info


# pylint: disable=logging-format-interpolation
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

  def __init__(self, show_memory_usage=False):
    """Initialize the foreman process.

    Args:
      show_memory_usage: Optional boolean value to indicate memory information
                         should be included in logging. The default is false.
    """
    super(Foreman, self).__init__()
    self._last_status_dict = {}
    self._process_information = process_info.ProcessInfo()
    self._process_labels = []
    self._processing_done = False
    self._show_memory_usage = show_memory_usage

  @property
  def labels(self):
    """Return a list of all currently watched labels."""
    return self._process_labels

  @property
  def number_of_processes_in_watch_list(self):
    """Return the number of processes in the watch list."""
    return len(self._process_labels)

  def CheckStatus(self, label=None):
    """Checks status of either a single process or all from the watch list.

    Args:
      label: A process label (instance of PROCESS_LABEL), if not provided
             all processes from the watch list are checked. Defaults to None.
    """
    if label is not None:
      self._CheckStatus(label)
      return

    for process_label in self._process_labels:
      self._CheckStatus(process_label)

  def GetLabel(self, name=None, pid=None):
    """Return a label if found using either name or PID value.

    Args:
      name: String value that should match an already existing label.
      pid: A process ID (PID) value for a process that is monitored.

    Returns:
      A label (instance of PROCESS_LABEL) if found. If neither name
      nor pid value is given or the process does not exist a None value
      will be returned.
    """
    if name is not None:
      for process_label in self._process_labels:
        if process_label.label == name:
          return process_label

    if pid is not None:
      for process_label in self._process_labels:
        if process_label.pid == pid:
          return process_label

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
    """
    if label is None:
      if pid is None or name is None:
        return
      label = self.PROCESS_LABEL(name, pid, process_info.ProcessInfo(pid=pid))

    if not label:
      return

    if label not in self._process_labels:
      self._process_labels.append(label)

  def StopMonitoringWorker(self, label=None, pid=None, name=None):
    """Stop monitoring a particular worker and remove it from monitor list.

    The purpose of this function is to remove a worker from the list of
    monitored workers. In order to do that the function requires either a
    label or a pid and a name.

    Args:
      label: A process label (instance of PROCESS_LABEL). Defaults to None, and
             so then a pid and name are required.
      pid: The process ID (PID) of the worker that should no longer be
           monitored. This is only required if label is not provided and
           defaults to None.
      name: The name of the worker process, defaults to None and is only
            required if label is not set.
    """
    if label is None:
      if pid is None or name is None:
        return
      label = self.PROCESS_LABEL(name, pid, process_info.ProcessInfo(pid=pid))

    if label not in self._process_labels:
      return

    index = self._process_labels.index(label)
    del self._process_labels[index]
    logging.info(
        u'{0:s} (PID: {1:d}) has been removed from foreman monitoring.'.format(
            label.label, label.pid))

  def SignalEndOfProcessing(self):
    """Indicate that processing is done."""
    self._processing_done = True
    # TODO: Reconsider this as an info signal. Should this not be moved to
    # a debug one?
    logging.info(
        u'Foreman received a signal indicating that processing is completed.')

    # This function may be called via RPC functions that expects a value to be
    # returned.
    return True

  def TerminateProcess(self, label=None, pid=None, name=None):
    """Terminate a process, even if it is not in the watch list.

    Args:
      label: A process label (instance of PROCESS_LABEL), if not provided
             then a pid and a name is required. It defaults to None, in which
             case you need to provide a pid and/or a name.
      pid: The process ID (PID) of the worker. This is only required if label
           is not provided and defaults to None.
      name: The name of the worker process, only required if label is not
            provided and defaults to None.
    """
    if label is not None:
      self._TerminateProcess(label)
      return

    if pid is not None:
      for process_label in self._process_labels:
        if process_label.pid == pid:
          self._TerminateProcess(process_label)
          return

    if name is not None:
      for process_label in self._process_labels:
        if process_label.label == name:
          self._TerminateProcess(process_label)
          return

    # If we reach here the process is not in our watch list.
    if pid is not None and name is not None:
      process_label = self.PROCESS_LABEL(
          name, pid, process_info.ProcessInfo(pid=pid))
      self._TerminateProcess(process_label)

  def _CheckStatus(self, label):
    """Check status for a single process from the watch list.

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
      label: A process label (instance of PROCESS_LABEL).
    """
    if label not in self._process_labels:
      return

    process = label.process

    if process.IsAlive():
      status_dict = process.GetProcessStatus()
      if not status_dict and not self._processing_done:
        logging.warning((
            u'Unable to connect to RPC socket to: {0:s} at '
            u'http://localhost:{1:d}').format(label.label, label.pid))

      if status_dict:
        self._last_status_dict[label.pid] = status_dict
        if status_dict.get(u'is_running', False):
          self._LogWorkerInformation(label, status_dict)
          if self._show_memory_usage:
            self._LogMemoryUsage(label)
          return

        else:
          logging.info((
              u'Process {0:s} (PID: {1:d}) has completed its processing. '
              u'Total of {2:d} events extracted').format(
                  label.label, label.pid, status_dict.get(u'counter', 0)))

    else:
      logging.info(u'Process {0:s} (PID: {1:d}) is not alive.'.format(
          label.label, label.pid))

    # Check if this process should be alive.
    if self._processing_done:
      # This process exited properly and should have. Let's remove it from our
      # list of labels.
      self.StopMonitoringWorker(label=label)
      return

    # We need to terminate the process.
    # TODO: Add a function to start a new instance of a worker instead of
    # just removing and killing it.
    logging.error((
        u'Process {0:s} (PID: {1:d}) is not functioning when it should be. '
        u'Terminating it and removing from list.').format(
            label.label, label.pid))
    self._TerminateProcess(label)

  def _LogMemoryUsage(self, label):
    """Logs memory information gathered from a process.

    This function will take a label and call the logging infrastructure to
    log information about the process's memory information.

    Args:
      label: A process label (instance of PROCESS_LABEL).
    """
    mem_info = label.process.GetMemoryInformation()
    logging.info((
        u'{0:s} - RSS: {1:d}, VMS: {2:d}, Shared: {3:d}, Text: {4:d}, lib: '
        u'{5:d}, data: {6:d}, dirty: {7:d}, Memory Percent: {8:0.2f}%').format(
            label.label, mem_info.rss, mem_info.vms, mem_info.shared,
            mem_info.text, mem_info.lib, mem_info.data, mem_info.dirty,
            mem_info.percent * 100))

  def _LogWorkerInformation(self, label, status=None):
    """Log information gathered from the worker.

    Args:
      label: A process label (instance of PROCESS_LABEL).
      status: Optional worker status dictonary. The default is None.
    """
    if status:
      # TODO: change file to "display name".
      logging.info((
          u'{0:s} (PID: {1:d}) - events extracted: {2:d} - file: {3:s} '
          u'- running: {4!s} <{5:s}>').format(
              label.label, label.pid, status.get(u'counter', -1),
              status.get(u'current_file', u''),
              status.get(u'is_running', False), label.process.status))

  def _TerminateProcess(self, label):
    """Terminate a process given a process label.

    Attempts to terminate a process and if successful removes the label from
    the watch list.

    Args:
      label: A process label (instance of PROCESS_LABEL).
    """
    if label is None:
      return

    label.process.TerminateProcess()

    # Double check the process is dead.
    if label.process.IsAlive():
      logging.warning(u'Process {0:s} (PID: {1:d}) is still alive.'.format(
          label.label, label.pid))
    elif label.process.status != 'exited':
      logging.warning(u'Process {0:s} (PID: {1:d}) may still be alive.'.format(
          label.label, label.pid))
    else:
      logging.info(u'Process: {0:s} (PID: {1:d}) has been terminated.'.format(
          label.label, label.pid))
      self.StopMonitoringWorker(label=label)
