# -*- coding: utf-8 -*-
"""The profiler classes."""

import abc
import os
import time

try:
  from guppy import hpy
except ImportError:
  hpy = None


class CPUTimeMeasurements(object):
  """The CPU time measurements.

  Attributes:
    number_of_samples (int): number of samples.
    total_cpu_time (int): total CPU time measured by the samples.
    total_system_time (int): total system time measured by the samples.
  """

  def __init__(self):
    """Initializes the CPU time measurements object."""
    super(CPUTimeMeasurements, self).__init__()
    self._cpu_time = None
    self._system_time = None
    self.number_of_samples = 0
    self.total_cpu_time = 0
    self.total_system_time = 0

  def SampleStart(self):
    """Starts measuring the CPU and system time."""
    self._cpu_time = time.clock()
    self._system_time = time.time()

  def SampleStop(self):
    """Stops the current measurement and adds the sample."""
    if self._cpu_time is None or self._system_time is None:
      return

    self.total_cpu_time += time.clock() - self._cpu_time
    self.total_system_time += time.time() - self._system_time
    self.number_of_samples += 1

    self._cpu_time = None
    self._system_time = None


class CPUTimeProfiler(object):
  """The CPU time profiler."""

  _FILENAME_PREFIX = u'cputime'

  def __init__(self, identifier, path=None):
    """Initializes the CPU time profiler object.

    Args:
      identifier (str): identifier of the profiling session used to create
          the sample filename.
      path (Optional[str]): path to write the sample file.
    """
    super(CPUTimeProfiler, self).__init__()
    self._identifier = identifier
    self._profile_measurements = {}
    self._sample_file = u'{0:s}-{1!s}.csv'.format(
        self._FILENAME_PREFIX, identifier)

    if path:
      self._sample_file = os.path.join(path, self._sample_file)

  def StartTiming(self, profile_name):
    """Starts timing CPU time.

    Args:
      profile_name (str): name of the profile to sample.
    """
    if profile_name not in self._profile_measurements:
      self._profile_measurements[profile_name] = CPUTimeMeasurements()

    self._profile_measurements[profile_name].SampleStart()

  def StopTiming(self, profile_name):
    """Stops timing CPU time.

    Args:
      profile_name (str): name of the profile to sample.
    """
    if profile_name not in self._profile_measurements:
      return

    self._profile_measurements[profile_name].SampleStop()

  def Write(self):
    """Writes the CPU time measurements to a sample file."""
    try:
      os.remove(self._sample_file)
    except OSError:
      pass

    with open(self._sample_file, 'wb') as file_object:
      line = (
          u'profile name\tnumber of samples\ttotal CPU time\t'
          u'total system time\n')
      file_object.write(line.encode(u'utf-8'))

      for name, measurements in iter(self._profile_measurements.items()):
        line = u'{0:s}\t{1!s}\t{2!s}\t{3!s}\n'.format(
            name, measurements.number_of_samples,
            measurements.total_cpu_time, measurements.total_system_time)

        file_object.write(line.encode(u'utf-8'))


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
    self._sample_file = u'{0!s}.hpy'.format(identifier)

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

  _FILENAME_PREFIX = u'parsers'


class ProcessingProfiler(CPUTimeProfiler):
  """The processing profiler."""

  _FILENAME_PREFIX = u'processing'


class SerializersProfiler(CPUTimeProfiler):
  """The serializers profiler."""

  _FILENAME_PREFIX = u'serializers'
