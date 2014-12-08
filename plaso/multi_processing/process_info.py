#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains a class to get process information."""

import collections
import os
import SocketServer

import psutil

from plaso.lib import timelib
from plaso.multi_processing import rpc_proxy


class ProcessInfo(object):
  """Class that provides information about a running process."""

  _MEMORY_INFORMATION = collections.namedtuple(
      'memory_information', 'rss vms shared text lib data dirty percent')

  def __init__(self, pid=None):
    """Initialize the process information object.

    Args:
      pid: Process ID (PID) value of the process to monitor. The default value
           is None in which case the PID of the calling
           process will be used.

    Raises:
      IOError: If the pid does not exist.
    """
    if pid is None:
      self._pid = os.getpid()
    else:
      self._pid = pid

    if not psutil.pid_exists(self._pid):
      raise IOError(u'Unable to read data from pid: {0:d}'.format(self._pid))

    self._command_line = ''
    self._parent = None
    self._process = psutil.Process(self._pid)
    if getattr(psutil, 'version_info', (0, 0, 0)) < (2, 0, 0):
      self._psutil_pre_v2 = True
    else:
      self._psutil_pre_v2 = False

    # TODO: Allow the client proxy object to determined at run time and not
    # a fixed value as here.
    self._rpc_client = rpc_proxy.StandardRpcProxyClient(self._pid)
    self._rpc_client.Open()

  @property
  def pid(self):
    """Return the process ID (PID)."""
    return self._pid

  @property
  def name(self):
    """Return the name of the process."""
    if self._psutil_pre_v2:
      return self._process.name

    return self._process.name()

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
  def parent(self):
    """Return a ProcessInfo object for the parent process."""
    if self._parent is not None:
      return self._parent

    try:
      if self._psutil_pre_v2:
        parent_pid = self._process.parent.pid
      else:
        parent = self._process.parent()   # pylint: disable-msg=not-callable
        parent_pid = parent.pid

      self._parent = ProcessInfo(pid=parent_pid)
      return self._parent
    except psutil.NoSuchProcess:
      return

  @property
  def open_files(self):
    """Yield a list of open files the process has."""
    try:
      for open_file in self._process.get_open_files():
        yield open_file.path
    except (psutil.AccessDenied, psutil.NoSuchProcess):
      return

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
  def number_of_threads(self):
    """Return back the number of threads this process has."""
    try:
      return self._process.get_num_threads()
    except psutil.NoSuchProcess:
      return 0

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
  def status(self):
    """Return the process status."""
    try:
      if self._psutil_pre_v2:
        return self._process.status
      else:
        return self._process.status()
    except psutil.NoSuchProcess:
      return u'exited'

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
  def io_counters(self):
    """Return back IO Counters for the process."""
    try:
      return self._process.get_io_counters()
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
  def cpu_percent(self):
    """Return back the percent of CPU processing this process consumes."""
    try:
      return self._process.get_cpu_percent()
    except psutil.NoSuchProcess:
      return

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
        getattr(external_information, 'rss', 0),
        getattr(external_information, 'vms', 0),
        getattr(external_information, 'shared', 0),
        getattr(external_information, 'text', 0),
        getattr(external_information, 'lib', 0),
        getattr(external_information, 'data', 0),
        getattr(external_information, 'dirty', 0), percent)

  def GetProcessStatus(self):
    """Attempt to connect to process via RPC to gather status information."""
    if self._rpc_client is None:
      return
    try:
      status = self._rpc_client.GetData('status')
      if isinstance(status, dict):
        return status
    except SocketServer.socket.error:
      return

  def IsAlive(self):
    """Return a boolean value indicating if the process is alive or not."""
    return self._process.is_running()

  def TerminateProcess(self):
    """Terminate the process."""
    # TODO: Make sure the process has really been terminated.
    if self.IsAlive():
      self._process.terminate()
