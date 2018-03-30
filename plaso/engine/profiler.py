# -*- coding: utf-8 -*-
"""The profiler classes."""

from __future__ import unicode_literals

import abc
import os
import time

try:
  from guppy import hpy
except ImportError:
  hpy = None


class CPUTimeMeasurement(object):
  """The CPU time measurement.

  Attributes:
    start_cpu_time (int): start CPU time.
    total_cpu_time (int): total CPU time.
  """

  def __init__(self):
    """Initializes the CPU time measurement."""
    super(CPUTimeMeasurement, self).__init__()
    self.start_cpu_time = None
    self.total_cpu_time = None

  def SampleStart(self):
    """Starts measuring the CPU and system time."""
    self.start_cpu_time = time.clock()
    self.total_cpu_time = 0

  def SampleStop(self):
    """Stops the current measurement and adds the sample."""
    if self.start_cpu_time is not None:
      self.total_cpu_time += time.clock() - self.start_cpu_time


class CPUTimeProfiler(object):
  """The CPU time profiler."""

  _FILENAME_PREFIX = 'cputime'

  def __init__(self, identifier, path=None):
    """Initializes the CPU time profiler object.

    Args:
      identifier (str): identifier of the profiling session used to create
          the sample filename.
      path (Optional[str]): path to write the sample file.
    """
    super(CPUTimeProfiler, self).__init__()
    self._identifier = identifier
    self._path = path
    self._profile_measurements = {}
    self._sample_file = '{0:s}-{1!s}.csv'.format(
        self._FILENAME_PREFIX, identifier)

    if path:
      self._sample_file = os.path.join(path, self._sample_file)

  def StartTiming(self, profile_name):
    """Starts timing CPU time.

    Args:
      profile_name (str): name of the profile to sample.
    """
    if profile_name not in self._profile_measurements:
      self._profile_measurements[profile_name] = CPUTimeMeasurement()

    self._profile_measurements[profile_name].SampleStart()

  def StopTiming(self, profile_name):
    """Stops timing CPU time.

    Args:
      profile_name (str): name of the profile to sample.
    """
    measurements = self._profile_measurements.get(profile_name)
    if measurements:
      measurements.SampleStop()

      sample = '{0:f}\t{1:s}\t{2:f}\n'.format(
          measurements.start_cpu_time, profile_name,
          measurements.total_cpu_time)
      self._sample_file.write(sample)

  def Start(self):
    """Starts the profiler."""
    filename = '{0:s}-{1:s}.csv.gz'.format(
        self._FILENAME_PREFIX, self._identifier)
    if self._path:
      filename = os.path.join(self._path, filename)

    self._sample_file = gzip.open(filename, 'wb')
    self._sample_file.write('CPU time\tName\tProcessing time\n')

  def Stop(self):
    """Stops the profiler."""
    self._sample_file.close()
    self._sample_file = None


class BaseMemoryProfiler(object):
  """The memory profiler interface."""

  def __init__(self, identifier, path=None, profiling_sample_rate=1000):
    """Initializes a memory profiler object.

    Args:
      identifier (str): unique name of the profile.
      profiling_sample_rate (Optional[int]): the profiling sample rate.
          Contains the number of event sources processed.
      path (Optional[str]): path to write the sample file.
    """
    super(BaseMemoryProfiler, self).__init__()
    self._identifier = identifier
    self._path = path
    self._profiling_sample = 0
    self._profiling_sample_rate = profiling_sample_rate

  @abc.abstractmethod
  def _Sample(self):
    """Takes a sample for profiling."""

  @classmethod
  def IsSupported(cls):
    """Determines if the profiler is supported.

    Returns:
      bool: True if the profiler is supported.
    """
    return False

  def Sample(self):
    """Takes a sample for profiling."""
    self._profiling_sample += 1

    if self._profiling_sample >= self._profiling_sample_rate:
      self._Sample()
      self._profiling_sample = 0

  @abc.abstractmethod
  def Start(self):
    """Starts the profiler."""

  @abc.abstractmethod
  def Stop(self):
    """Stops the profiler."""


class GuppyMemoryProfiler(BaseMemoryProfiler):
  """The guppy-based memory profiler."""

  def __init__(self, identifier, path=None, profiling_sample_rate=1000):
    """Initializes a memory profiler object.

    Args:
      identifier (str): unique name of the profile.
      path (Optional[str]): path to write the sample file.
      profiling_sample_rate (Optional[int]): the profiling sample rate.
          Contains the number of event sources processed.
    """
    super(GuppyMemoryProfiler, self).__init__(
        identifier, path=path, profiling_sample_rate=profiling_sample_rate)
    self._heapy = None
    self._sample_file = '{0!s}.hpy'.format(identifier)

    if self._path:
      self._sample_file = os.path.join(self._path, self._sample_file)

    if hpy:
      self._heapy = hpy()

  def _Sample(self):
    """Takes a sample for profiling."""
    if not self._heapy:
      return

    heap = self._heapy.heap()
    heap.dump(self._sample_file)

  @classmethod
  def IsSupported(cls):
    """Determines if the profiler is supported.

    Returns:
      bool: True if the profiler is supported.
    """
    return hpy is not None

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


class ParsersProfiler(CPUTimeProfiler):
  """The parsers profiler."""

  _FILENAME_PREFIX = 'parsers'


class ProcessingProfiler(CPUTimeProfiler):
  """The processing profiler."""

  _FILENAME_PREFIX = 'processing'


class SerializersProfiler(CPUTimeProfiler):
  """The serializers profiler."""

  _FILENAME_PREFIX = 'serializers'
