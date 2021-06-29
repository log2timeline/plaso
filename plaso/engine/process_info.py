# -*- coding: utf-8 -*-
"""Information about running process."""

import psutil


class ProcessInfo(object):
  """Provides information about a running process."""

  def __init__(self, pid):
    """Initializes process information.

    Args:
      pid (int): process identifier (PID).

    Raises:
      IOError: If the process identified by the PID does not exist.
      OSError: If the process identified by the PID does not exist.
    """
    if not psutil.pid_exists(pid):
      raise IOError('Process with PID: {0:d} does not exist'.format(pid))

    self._process = psutil.Process(pid)

  def GetUsedMemory(self):
    """Retrieves the amount of memory used by the process.

    Returns:
      int: amount of memory in bytes used by the process or None
          if not available.
    """
    try:
      memory_info = self._process.memory_info()
    except psutil.NoSuchProcess:
      return None

    # Psutil will return different memory information depending on what is
    # available in that platform.
    memory_data = getattr(memory_info, 'data', 0)
    memory_shared = getattr(memory_info, 'shared', 0)

    return memory_data + memory_shared
