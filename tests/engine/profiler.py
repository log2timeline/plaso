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
from plaso.engine import profiler

from tests import test_lib as shared_test_lib


class CPUTimeMeasurementTest(shared_test_lib.BaseTestCase):
  """Tests for the CPU time measurement."""

  def testSampleStartStop(self):
    """Tests the SampleStart and SampleStop functions."""
    cpu_measurement = profiler.CPUTimeMeasurement()
    cpu_measurement.SampleStart()
    cpu_measurement.SampleStop()


class SampleFileProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the shared functionality for sample file-based profilers."""

  # pylint: disable=protected-access

  def testIsSupported(self):
    """Tests the IsSupported function."""
    self.assertTrue(profiler.SampleFileProfiler.IsSupported())

  def testStartStop(self):
    """Tests the Start and Stop functions."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profiler.SampleFileProfiler(
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

      test_profiler = profiler.CPUTimeProfiler(
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
    self.assertTrue(profiler.GuppyMemoryProfiler.IsSupported())

    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory
      profiling_configuration.profiling_sample_rate = 1000

      test_profiler = profiler.GuppyMemoryProfiler(
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

      test_profiler = profiler.MemoryProfiler(
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

      test_profiler = profiler.ParsersProfiler(
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

      test_profiler = profiler.ProcessingProfiler(
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

      test_profiler = profiler.SerializersProfiler(
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

      test_profiler = profiler.StorageProfiler(
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

      test_profiler = profiler.TaskQueueProfiler(
          'test', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.Sample(task_status)
        time.sleep(0.01)

      test_profiler.Stop()


if __name__ == '__main__':
  unittest.main()
