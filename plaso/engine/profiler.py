# -*- coding: utf-8 -*-
"""The profiler classes."""

import abc
import os
import time

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


class ParserMeasurements(object):
  """The parser measurements."""

  def __init__(self):
    """Initializes the parser measurements object."""
    super(ParserMeasurements, self).__init__()
    self.number_of_samples = 0
    self.total_cpu_time = 0
    self.total_system_time = 0

  def AddSample(self, cpu_time, system_time):
    """Adds a measurement sample.

    Args:
      cpu_time: the duration of the parser run in CPU time.
      system_time: the duration of the parser run in system time.
    """
    self.number_of_samples += 1
    self.total_cpu_time += cpu_time
    self.total_system_time += system_time


class ParsersProfiler(object):
  """The parsers profiler."""

  def __init__(self, identifier):
    """Initializes the parsers profiler object.

    Args:
      identifier: the profile identifier.
    """
    super(ParsersProfiler, self).__init__()
    self._cpu_time = None
    self._identifier = identifier
    self._parser_name = None
    self._parser_measurements = {}
    self._sample_file = u'parsers-{0!s}.csv'.format(identifier)
    self._system_time = None

  def StopTiming(self):
    """Stops timing a parser."""
    cpu_time = time.clock() - self._cpu_time
    system_time = time.time() - self._system_time

    parser_measurements = self._parser_measurements[self._parser_name]
    parser_measurements.AddSample(cpu_time, system_time)

    self._cpu_time = None
    self._parser_name = None
    self._system_time = None

  def StartTiming(self, parser_name):
    """Starts timing a parser.

    Args:
      parser_name: the name of the parser to sample.
    """
    if parser_name not in self._parser_measurements:
      self._parser_measurements[parser_name] = ParserMeasurements()

    self._cpu_time = time.clock()
    self._parser_name = parser_name
    self._system_time = time.time()

  def Write(self):
    """Writes the parser measurements to a sample file."""
    try:
      os.remove(self._sample_file)
    except OSError:
      pass

    with open(self._sample_file, 'wb') as file_object:
      line = (
          u'parser name\tnumber of samples\ttotal CPU time\t'
          u'total system time\n')
      file_object.write(line.encode(u'utf-8'))

      for name, parser_measurements in self._parser_measurements.iteritems():
        line = u'{0:s}\t{1!s}\t{2!s}\t{3!s}\n'.format(
            name, parser_measurements.number_of_samples,
            parser_measurements.total_cpu_time,
            parser_measurements.total_system_time)

        file_object.write(line.encode(u'utf-8'))
