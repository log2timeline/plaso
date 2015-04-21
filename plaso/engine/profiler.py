# -*- coding: utf-8 -*-
"""The profiler classes."""

import abc
import os

try:
  from guppy import hpy
except ImportError:
  hpy = None


class BaseMemoryProfiler(object):
  """The memory profiler interface."""

  def __init__(self, identifier):
    """Initializes the memory profiler object.

    Args:
      identifier: the profile identifier.
    """
    super(BaseMemoryProfiler, self).__init__()
    self._identifier = identifier

  @classmethod
  def IsSupported(cls):
    """Returns a boolean value to indicate the profiler is supported."""
    return False

  @abc.abstractmethod
  def Sample(self, data):
    """Takes a sample for profiling.

    Args:
      data: the sample data.
    """

  @abc.abstractmethod
  def Start(self):
    """Starts the profiler."""

  @abc.abstractmethod
  def Stop(self):
    """Stops the profiler."""


class GuppyMemoryProfiler(BaseMemoryProfiler):
  """The guppy-based memory profiler interface."""

  def __init__(self, identifier):
    """Initializes the memory profiler object.

    Args:
      identifier: the profile identifier.
    """
    super(GuppyMemoryProfiler, self).__init__(identifier)
    self._sample_file = u'{0!s}.hpy'.format(identifier)

    if hpy:
      self._heapy = hpy()
    else:
      self._heapy = None

  @classmethod
  def IsSupported(cls):
    """Returns a boolean value to indicate the profiler is supported."""
    return hpy is not None

  def Sample(self, unused_data):
    """Takes a sample for profiling.

    Args:
      data: the sample data.
    """
    if not self._heapy:
      return

    heap = self._heapy.heap()
    heap.dump(self._sample_file)

  def Start(self):
    """Starts the profiler."""
    if not self._heapy:
      return

    self._heapy.setrelheap()

    try:
      os.remove(self._sample_file)
    except OSError:
      pass

  def Stop(self):
    """Stops the profiler."""
    return
