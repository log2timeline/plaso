# -*- coding: utf-8 -*-
"""This file contains a class to get process information."""

import collections

import psutil


class ProcessInfo(object):
  """Class that provides information about a running process."""

  _MEMORY_INFORMATION = collections.namedtuple(
      u'memory_information', u'rss vms shared text lib data dirty percent')

  STATUS_DEAD = getattr(psutil, u'STATUS_DEAD', u'dead')
  STATUS_EXITED = u'exited'
  STATUS_SLEEPING = getattr(psutil, u'STATUS_SLEEPING', u'sleeping')
  STATUS_DISK_SLEEP = getattr(psutil, u'STATUS_DISK_SLEEP', u'disk-sleep')
  STATUS_STOPPED = getattr(psutil, u'STATUS_STOPPED', u'stopped')
  STATUS_IDLE = getattr(psutil, u'STATUS_IDLE', u'idle')
  STATUS_TRACING_STOP = getattr(psutil, u'STATUS_TRACING_STOP', u'tracing-stop')
  STATUS_LOCKED = getattr(psutil, u'STATUS_LOCKED', u'locked')
  STATUS_WAKING = getattr(psutil, u'STATUS_WAKING', u'waking')
  STATUS_RUNNING = getattr(psutil, u'STATUS_RUNNING', u'running')
  STATUS_ZOMBIE = getattr(psutil, u'STATUS_ZOMBIE', u'zombie')

  def __init__(self, pid):
    """Initialize the process information object.

    Args:
      pid: The process ID (PID).

    Raises:
      IOError: If the process identified by the PID does not exist.
    """
    if not psutil.pid_exists(pid):
      raise IOError(u'Process with PID: {0:d} does not exist'.format(pid))

    self._process = psutil.Process(pid)
    if getattr(psutil, u'version_info', (0, 0, 0)) < (2, 0, 0):
      self._psutil_pre_v2 = True
    else:
      self._psutil_pre_v2 = False

  @property
  def status(self):
    """Return the process status."""
    try:
      if self._psutil_pre_v2:
        return self._process.status
      else:
        return self._process.status()  # pylint: disable=not-callable
    except psutil.NoSuchProcess:
      return self.STATUS_EXITED

  def GetMemoryInformation(self):
    """Return back memory information as a memory_information object.

    Returns:
      Memory information object (instance of memory_information) a named
      tuple that contains the following attributes: rss, vms, shared, text,
      lib, data, dirty, percent.
    """
    try:
      external_information = self._process.get_ext_memory_info()
    except psutil.NoSuchProcess:
      return

    percent = self._process.get_memory_percent()

    # Psutil will return different memory information depending on what is
    # available in that platform.
    # TODO: Not be as strict in what gets returned, have this object more
    # flexible so that the memory information returned reflects the available
    # information in the platform.
    return self._MEMORY_INFORMATION(
        getattr(external_information, u'rss', 0),
        getattr(external_information, u'vms', 0),
        getattr(external_information, u'shared', 0),
        getattr(external_information, u'text', 0),
        getattr(external_information, u'lib', 0),
        getattr(external_information, u'data', 0),
        getattr(external_information, u'dirty', 0), percent)
