#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the profiler classes."""

from __future__ import unicode_literals

import time
import unittest

try:
  from guppy import hpy
except ImportError:
  hpy = None

from plaso.engine import configurations
from plaso.engine import processing_status
from plaso.engine import profilers

from tests import test_lib as shared_test_lib


class CPUTimeMeasurementTest(shared_test_lib.BaseTestCase):
  """Tests for the CPU time measurement."""

  def testSampleStartStop(self):
    """Tests the SampleStart and SampleStop functions."""
    cpu_measurement = profilers.CPUTimeMeasurement()
    cpu_measurement.SampleStart(0.0)
    cpu_measurement.SampleStop()


class SampleFileProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the shared functionality for sample file-based profilers."""

  # pylint: disable=protected-access

  def testIsSupported(self):
    """Tests the IsSupported function."""
    self.assertTrue(profilers.SampleFileProfiler.IsSupported())

  def testGetSampleTime(self):
    """Tests the _GetSampleTime function."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profilers.SampleFileProfiler(
          'test', profiling_configuration)

      test_profiler._FILE_HEADER = 'test'

      sample_time = test_profiler._GetSampleTime()
      self.assertIsNone(sample_time)

      test_profiler.Start()

      sample_time = test_profiler._GetSampleTime()
      self.assertIsNotNone(sample_time)

      test_profiler.Stop()

  def testStartStop(self):
    """Tests the Start and Stop functions."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profilers.SampleFileProfiler(
          'test', profiling_configuration)

      test_profiler._FILE_HEADER = 'test'

      test_profiler.Start()

      test_profiler.Stop()


class CPUTimeProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the CPU time profiler."""

  def testStartStopTiming(self):
    """Tests the StartTiming and StopTiming functions."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profilers.CPUTimeProfiler(
          'test', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.StartTiming('test_profile')
        time.sleep(0.01)
        test_profiler.StopTiming('test_profile')

      test_profiler.Stop()


# Note that this test can be extremely slow with guppy version 0.1.9
# use version 0.1.10 or later.
@unittest.skipIf(not hpy, 'missing guppy.hpy')
class GuppyMemoryProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the guppy-based memory profiler."""

  def testStartSampleStop(self):
    """Tests the Start, Sample and Stop functions."""
    self.assertTrue(profilers.GuppyMemoryProfiler.IsSupported())

    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory
      profiling_configuration.profiling_sample_rate = 1000

      test_profiler = profilers.GuppyMemoryProfiler(
          'test', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.Sample()
        time.sleep(0.01)

      test_profiler.Stop()


class MemoryProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the memory profiler."""

  def testSample(self):
    """Tests the Sample function."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profilers.MemoryProfiler(
          'test', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.Sample(400)
        time.sleep(0.01)

      test_profiler.Stop()


class ParsersProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the parsers CPU time profiler."""

  def testStartStopTiming(self):
    """Tests the StartTiming and StopTiming functions."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profilers.ParsersProfiler(
          'test', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.StartTiming('test_profile')
        time.sleep(0.01)
        test_profiler.StopTiming('test_profile')

      test_profiler.Stop()


class ProcessingProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the processing CPU time profiler."""

  def testStartStopTiming(self):
    """Tests the StartTiming and StopTiming functions."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profilers.ProcessingProfiler(
          'test', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.StartTiming('test_profile')
        time.sleep(0.01)
        test_profiler.StopTiming('test_profile')

      test_profiler.Stop()


class SerializersProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the serializers CPU time profiler."""

  def testStartStopTiming(self):
    """Tests the StartTiming and StopTiming functions."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profilers.SerializersProfiler(
          'test', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.StartTiming('test_profile')
        time.sleep(0.01)
        test_profiler.StopTiming('test_profile')

      test_profiler.Stop()


class StorageProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the storage profiler."""

  def testSample(self):
    """Tests the Sample function."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profilers.StorageProfiler(
          'test', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.Sample('read', 'test', 1024, 128)
        time.sleep(0.01)

      test_profiler.Stop()


class TaskQueueProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the task queue profiler."""

  def testSample(self):
    """Tests the Sample function."""
    task_status = processing_status.TasksStatus()

    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profilers.TaskQueueProfiler(
          'test', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.Sample(task_status)
        time.sleep(0.01)

      test_profiler.Stop()


if __name__ == '__main__':
  unittest.main()
