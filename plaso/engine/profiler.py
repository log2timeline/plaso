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
  """The CPU time measurements."""

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

  def __init__(self, identifier):
    """Initializes the CPU time profiler object.

    Args:
      identifier: the profile identifier.
    """
    super(CPUTimeProfiler, self).__init__()
    self._identifier = identifier
    self._profile_measurements = {}
    self._sample_file = u'{0:s}-{1!s}.csv'.format(
        self._FILENAME_PREFIX, identifier)

  def StopTiming(self, profile_name):
    """Stops timing CPU time.

    Args:
      profile_name: the name of the profile to sample.
    """
    if profile_name not in self._profile_measurements:
      return

    self._profile_measurements[profile_name].SampleStop()

  def StartTiming(self, profile_name):
    """Starts timing CPU time.

    Args:
      profile_name: the name of the profile to sample.
    """
    if profile_name not in self._profile_measurements:
      self._profile_measurements[profile_name] = CPUTimeMeasurements()

    self._profile_measurements[profile_name].SampleStart()

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

      for name, profile_measurements in self._profile_measurements.iteritems():
        line = u'{0:s}\t{1!s}\t{2!s}\t{3!s}\n'.format(
            name, profile_measurements.number_of_samples,
            profile_measurements.total_cpu_time,
            profile_measurements.total_system_time)

        file_object.write(line.encode(u'utf-8'))


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
  def Sample(self):
    """Takes a sample for profiling."""

  @abc.abstractmethod
  def Start(self):
    """Starts the profiler."""

  @abc.abstractmethod
  def Stop(self):
    """Stops the profiler."""


class GuppyMemoryProfiler(BaseMemoryProfiler):
  """The guppy-based memory profiler."""

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

  def Sample(self):
    """Takes a sample for profiling."""
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


class ParsersProfiler(CPUTimeProfiler):
  """The parsers profiler."""

  _FILENAME_PREFIX = u'parsers'


class SerializersProfiler(CPUTimeProfiler):
  """The serializers profiler."""

  _FILENAME_PREFIX = u'serializers'
