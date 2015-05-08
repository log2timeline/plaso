# -*- coding: utf-8 -*-
"""This file contains a class to get process information."""

import collections

import psutil

from plaso.lib import timelib


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

    self._command_line = u''
    self._parent = None
    self._pid = pid
    self._process = psutil.Process(pid)
    if getattr(psutil, u'version_info', (0, 0, 0)) < (2, 0, 0):
      self._psutil_pre_v2 = True
    else:
      self._psutil_pre_v2 = False

  @property
  def children(self):
    """Yield all child processes as a ProcessInfo object."""
    try:
      for child in self._process.get_children():
        yield ProcessInfo(pid=child.pid)
    except psutil.NoSuchProcess:
      # We are creating an empty generator here. Yield or return None
      # individually don't provide that behavior, neither does raising
      # GeneratorExit or StopIteration.
      # pylint: disable=unreachable
      return
      yield

  @property
  def command_line(self):
    """Return the full command line used to start the process."""
    if self._command_line:
      return self._command_line

    try:
      if self._psutil_pre_v2:
        command_lines = self._process.cmdline
      else:
        command_lines = self._process.cmdline()

      self._command_line = u' '.join(command_lines)
    except psutil.NoSuchProcess:
      return

    return self._command_line

  @property
  def cpu_percent(self):
    """Return back the percent of CPU processing this process consumes."""
    try:
      return self._process.get_cpu_percent()
    except psutil.NoSuchProcess:
      return

  @property
  def cpu_times(self):
    """Return back CPU times for the process."""
    try:
      return self._process.get_cpu_times()
    except psutil.NoSuchProcess:
      return

  @property
  def memory_map(self):
    """Yield memory map objects (instance of mmap)."""
    try:
      for memory_map in self._process.get_memory_maps():
        yield memory_map
    except psutil.NoSuchProcess:
      # We are creating an empty generator here. Yield or return None
      # individually don't provide that behavior, neither does raising
      # GeneratorExit or StopIteration.
      # pylint: disable=unreachable
      return
      yield

  @property
  def name(self):
    """Return the name of the process."""
    if self._psutil_pre_v2:
      return self._process.name

    return self._process.name()

  @property
  def number_of_threads(self):
    """Return back the number of threads this process has."""
    try:
      return self._process.get_num_threads()
    except psutil.NoSuchProcess:
      return 0

  @property
  def open_files(self):
    """Yield a list of open files the process has."""
    try:
      for open_file in self._process.get_open_files():
        yield open_file.path
    except (psutil.AccessDenied, psutil.NoSuchProcess):
      return

  @property
  def parent(self):
    """Return a ProcessInfo object for the parent process."""
    if self._parent is not None:
      return self._parent

    try:
      if self._psutil_pre_v2:
        parent_pid = self._process.parent.pid
      else:
        parent = self._process.parent()   # pylint: disable=not-callable
        parent_pid = parent.pid

      self._parent = ProcessInfo(pid=parent_pid)
      return self._parent
    except psutil.NoSuchProcess:
      return

  @property
  def pid(self):
    """Return the process ID (PID)."""
    return self._pid

  @property
  def start_time(self):
    """Return back the start time of the process.

    Returns:
      An integer representing the number of microseconds since Unix Epoch time
      in UTC.
    """
    if self._psutil_pre_v2:
      create_time = self._process.create_time
    else:
      create_time = self._process.create_time()
    return timelib.Timestamp.FromPosixTime(int(create_time))

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

  def IsAlive(self):
    """Return a boolean value indicating if the process is alive or not."""
    return self._process.is_running()

  def TerminateProcess(self):
    """Terminate the process."""
    # TODO: Make sure the process has really been terminated.
    if self.IsAlive():
      self._process.terminate()
