# -*- coding: utf-8 -*-
"""This file contains a class to get process information."""

import psutil


class ProcessInfo(object):
  """Provides information about a running process."""

  def __init__(self, pid):
    """Initializes process information.

    Args:
      pid (int): process identifier (PID).

    Raises:
      IOError: If the process identified by the PID does not exist.
    """
    if not psutil.pid_exists(pid):
      raise IOError(u'Process with PID: {0:d} does not exist'.format(pid))

    self._memory_info_function = None
    self._process = psutil.Process(pid)

    version = getattr(psutil, u'version_info', (0, 0, 0))
    if version < (2, 0, 0):
      self._memory_info_function = self._process.get_ext_memory_info
    else:
      self._memory_info_function = self._process.memory_info_ex

  def GetUsedMemory(self):
    """Retrieves the amount of memory used by the process.

    Returns:
      int: amount of memory in bytes used by the process or None
          if not available.
    """
    try:
      memory_info = self._memory_info_function()
    except psutil.NoSuchProcess:
      return

    # Psutil will return different memory information depending on what is
    # available in that platform.
    memory_data = getattr(memory_info, u'data', 0)
    memory_shared = getattr(memory_info, u'shared', 0)

    return memory_data + memory_shared
