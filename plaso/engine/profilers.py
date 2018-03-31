# -*- coding: utf-8 -*-
"""The profiler classes."""

from __future__ import unicode_literals

import gzip
import os
import time

try:
  from guppy import hpy
except ImportError:
  hpy = None


class CPUTimeMeasurement(object):
  """The CPU time measurement.

  Attributes:
    sample_start_time (float): start sample time or None if not set.
    total_cpu_time (float): total CPU time or None if not set.
  """

  def __init__(self):
    """Initializes the CPU time measurement."""
    super(CPUTimeMeasurement, self).__init__()
    self._start_cpu_time = None
    self.start_sample_time = None
    self.total_cpu_time = None

  def SampleStart(self):
    """Starts measuring the CPU time."""
    self._start_cpu_time = time.clock()
    self.start_sample_time = time.time()
    self.total_cpu_time = 0

  def SampleStop(self):
    """Stops measuring the CPU time."""
    if self._start_cpu_time is not None:
      self.total_cpu_time += time.clock() - self._start_cpu_time


class SampleFileProfiler(object):
  """Shared functionality for sample file-based profilers."""

  _FILENAME_PREFIX = None

  _FILE_HEADER = None

  def __init__(self, identifier, configuration):
    """Initializes the sample file profiler.

    Args:
      identifier (str): identifier of the profiling session used to create
          the sample filename.
      configuration (ProfilingConfiguration): profiling configuration.
    """
    super(SampleFileProfiler, self).__init__()
    self._identifier = identifier
    self._path = configuration.directory
    self._profile_measurements = {}
    self._sample_file = None
    self._start_time = None

  @classmethod
  def IsSupported(cls):
    """Determines if the profiler is supported.

    Returns:
      bool: True if the profiler is supported.
    """
    return True

  def Start(self):
    """Starts the profiler."""
    filename = '{0:s}-{1:s}.csv.gz'.format(
        self._FILENAME_PREFIX, self._identifier)
    if self._path:
      filename = os.path.join(self._path, filename)

    self._sample_file = gzip.open(filename, 'wb')
    self._sample_file.write(self._FILE_HEADER)

    self._start_time = time.time()

  def Stop(self):
    """Stops the profiler."""
    self._sample_file.close()
    self._sample_file = None


class CPUTimeProfiler(SampleFileProfiler):
  """The CPU time profiler."""

  _FILENAME_PREFIX = 'cputime'

  _FILE_HEADER = 'Time\tName\tProcessing time\n'

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
          measurements.start_sample_time, profile_name,
          measurements.total_cpu_time)
      self._sample_file.write(sample)


class GuppyMemoryProfiler(object):
  """The guppy-based memory profiler."""

  def __init__(self, identifier, configuration):
    """Initializes a memory profiler.

    Args:
      identifier (str): unique name of the profile.
      configuration (ProfilingConfiguration): profiling configuration.
    """
    super(GuppyMemoryProfiler, self).__init__()
    self._identifier = identifier
    self._path = configuration.directory
    self._profiling_sample = 0
    self._profiling_sample_rate = configuration.profiling_sample_rate
    self._heapy = None
    self._sample_file = '{0!s}.hpy'.format(identifier)

    if self._path:
      self._sample_file = os.path.join(self._path, self._sample_file)

    if hpy:
      self._heapy = hpy()

  @classmethod
  def IsSupported(cls):
    """Determines if the profiler is supported.

    Returns:
      bool: True if the profiler is supported.
    """
    return hpy is not None

  def Sample(self):
    """Takes a sample for profiling."""
    self._profiling_sample += 1

    if self._profiling_sample >= self._profiling_sample_rate:
      if self._heapy:
        heap = self._heapy.heap()
        heap.dump(self._sample_file)

      self._profiling_sample = 0

  def Start(self):
    """Starts the profiler."""
    if self._heapy:
      self._heapy.setrelheap()

      try:
        os.remove(self._sample_file)
      except OSError:
        pass

  def Stop(self):
    """Stops the profiler."""
    return


class MemoryProfiler(SampleFileProfiler):
  """The memory profiler."""

  _FILENAME_PREFIX = 'memory'

  _FILE_HEADER = 'Time\tUsed memory\n'

  def Sample(self, used_memory):
    """Takes a sample for profiling.

    Args:
      used_memory (int): amount of used memory in bytes.
    """
    sample_time = time.time()
    sample = '{0:f}\t{1:d}\n'.format(sample_time, used_memory)
    self._sample_file.write(sample)


class ParsersProfiler(CPUTimeProfiler):
  """The parsers profiler."""

  _FILENAME_PREFIX = 'parsers'


class ProcessingProfiler(CPUTimeProfiler):
  """The processing profiler."""

  _FILENAME_PREFIX = 'processing'


class SerializersProfiler(CPUTimeProfiler):
  """The serializers profiler."""

  _FILENAME_PREFIX = 'serializers'


class StorageProfiler(SampleFileProfiler):
  """The storage profiler."""

  _FILENAME_PREFIX = 'storage'

  _FILE_HEADER = (
      'Time\tOperation\tDescription\tData size\tCompressed data size\n')

  def Sample(self, operation, description, data_size, compressed_data_size):
    """Takes a sample of data read or written for profiling.

    Args:
      operation (str): operation, either 'read' or 'write'.
      description (str): description of the data read.
      data_size (int): size of the data read in bytes.
      compressed_data_size (int): size of the compressed data read in bytes.
    """
    sample_time = time.time()
    sample = '{0:f}\t{1:s}\t{2:s}\t{3:d}\t{4:d}\n'.format(
        sample_time, operation, description, data_size, compressed_data_size)
    self._sample_file.write(sample)


class TaskQueueProfiler(SampleFileProfiler):
  """The task queue profiler."""

  _FILENAME_PREFIX = 'task_queue'

  _FILE_HEADER = (
      'Time\tQueued\tProcessing\tTo merge\tAbandoned\tTotal\n')

  def Sample(self, tasks_status):
    """Takes a sample of the status of queued tasks for profiling.

    Args:
      tasks_status (TasksStatus): status information about tasks.
    """
    sample_time = time.time()
    sample = '{0:f}\t{1:d}\t{2:d}\t{3:d}\t{4:d}\t{5:d}\n'.format(
        sample_time, tasks_status.number_of_queued_tasks,
        tasks_status.number_of_tasks_processing,
        tasks_status.number_of_tasks_pending_merge,
        tasks_status.number_of_abandoned_tasks,
        tasks_status.total_number_of_tasks)
    self._sample_file.write(sample)
