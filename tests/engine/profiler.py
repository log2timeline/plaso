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
from plaso.engine import profiler

from tests import test_lib as shared_test_lib


class CPUTimeProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the CPU time profiler."""

  def testCPUTimeProfiler(self):
    """Tests the StartTiming, StopTiming, Start and Stop functions."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profiler.CPUTimeProfiler(
          'unittest', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.StartTiming('test_profile')
        time.sleep(0.01)
        test_profiler.StopTiming('test_profile')

      test_profiler.Stop()


class MemoryProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the memory profiler."""

  def testMemoryProfiler(self):
    """Tests the Sample, Start and Stop functions."""
    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profiler.MemoryProfiler(
          'unittest', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.Sample(400)
        time.sleep(0.01)

      test_profiler.Stop()


# Note that this test can be extremely slow with guppy version 0.1.9
# use version 0.1.10 or later.
@unittest.skipIf(not hpy, 'missing guppy.hpy')
class GuppyMemoryProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the guppy-based memory profiler."""

  def testGuppyMemoryProfiler(self):
    """Tests the Start, Sample and Stop functions."""
    self.assertTrue(profiler.GuppyMemoryProfiler.IsSupported())

    profiling_configuration = configurations.ProfilingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      profiling_configuration.directory = temp_directory

      test_profiler = profiler.GuppyMemoryProfiler(
          'unittest', profiling_configuration)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.Sample()
        time.sleep(0.01)

      test_profiler.Stop()


if __name__ == '__main__':
  unittest.main()
