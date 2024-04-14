# -*- coding: utf-8 -*-
"""The profiler classes."""

import codecs
import gzip
import os
import time


class CPUTimeMeasurement(object):
  """The CPU time measurement.

  Attributes:
    start_sample_time (float): start sample time or None if not set.
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
    self._start_cpu_time = time.perf_counter()
    self.start_sample_time = time.time()
    self.total_cpu_time = 0

  def SampleStop(self):
    """Stops measuring the CPU time."""
    if self._start_cpu_time is not None:
      self.total_cpu_time += time.perf_counter() - self._start_cpu_time


class SampleFileProfiler(object):
  """Shared functionality for sample file-based profilers."""


  # This constant must be overridden by subclasses.
  _FILENAME_PREFIX = None

  # This constant must be overridden by subclasses.
  _FILE_HEADER = None

  def __init__(self, identifier, configuration):
    """Initializes a sample file profiler.

    Sample files are gzip compressed UTF-8 encoded CSV files.

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

  def _WritesString(self, content):
    """Writes a string to the sample file.

    Args:
      content (str): content to write to the sample file.
    """
    content_bytes = codecs.encode(content, 'utf-8')
    self._sample_file.write(content_bytes)

  @classmethod
  def IsSupported(cls):
    """Determines if the profiler is supported.

    Returns:
      bool: True if the profiler is supported.
    """
    return True

  def Start(self):
    """Starts the profiler."""
    filename = f'{self._FILENAME_PREFIX:s}-{self._identifier:s}.csv.gz'
    if self._path:
      filename = os.path.join(self._path, filename)

    self._sample_file = gzip.open(filename, 'wb')
    self._WritesString(self._FILE_HEADER)

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

      self._WritesString((
          f'{measurements.start_sample_time:f}\t{profile_name:s}\t'
          f'{measurements.total_cpu_time:f}\n'))


class MemoryProfiler(SampleFileProfiler):
  """The memory profiler."""

  _FILENAME_PREFIX = 'memory'

  _FILE_HEADER = 'Time\tName\tUsed memory\n'

  def Sample(self, profile_name, used_memory):
    """Takes a sample for profiling.

    Args:
      profile_name (str): name of the profile to sample.
      used_memory (int): amount of used memory in bytes.
    """
    sample_time = time.time()
    self._WritesString(f'{sample_time:f}\t{profile_name:s}\t{used_memory:d}\n')


class AnalyzersProfiler(CPUTimeProfiler):
  """The analyzers profiler."""

  _FILENAME_PREFIX = 'analyzers'


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
      'Time\tName\tOperation\tDescription\tProcessing time\tData size\t'
      'Compressed data size\n')

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

  def Sample(
      self, profile_name, operation, description, data_size,
      compressed_data_size):
    """Takes a sample of data read or written for profiling.

    Args:
      profile_name (str): name of the profile to sample.
      operation (str): operation, either 'read' or 'write'.
      description (str): description of the data read.
      data_size (int): size of the data read in bytes.
      compressed_data_size (int): size of the compressed data read in bytes.
    """
    measurements = self._profile_measurements.get(profile_name)
    if measurements:
      sample_time = measurements.start_sample_time
      processing_time = measurements.total_cpu_time
    else:
      sample_time = time.time()
      processing_time = 0.0

    self._WritesString((
        f'{sample_time:f}\t{profile_name:s}\t{operation:s}\t{description:s}\t'
        f'{processing_time:f}\t{data_size:d}\t{compressed_data_size:d}\n'))


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
    self._WritesString((
        f'{sample_time:f}\t{tasks_status.number_of_queued_tasks:d}\t'
        f'{tasks_status.number_of_tasks_processing:d}\t'
        f'{tasks_status.number_of_tasks_pending_merge:d}\t'
        f'{tasks_status.number_of_abandoned_tasks:d}\t'
        f'{tasks_status.total_number_of_tasks:d}\n'))


class TasksProfiler(SampleFileProfiler):
  """The tasks profiler."""

  _FILENAME_PREFIX = 'tasks'

  _FILE_HEADER = 'Time\tIdentifier\tStatus\n'

  def Sample(self, task, status):
    """Takes a sample of the status of a task for profiling.

    Args:
      task (Task): a task.
      status (str): status.
    """
    sample_time = time.time()
    self._WritesString(f'{sample_time:f}\t{task.identifier:s}\t{status:s}\n')
