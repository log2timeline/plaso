#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the profiler classes."""

import time
import unittest

try:
  from guppy import hpy
except ImportError:
  hpy = None

from plaso.engine import profiler

from tests import test_lib as shared_test_lib


class CPUTimeProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the CPU time profiler."""

  def testCPUTimeProfiler(self):
    """Tests the StartTiming, StopTiming and Write functions."""
    with shared_test_lib.TempDirectory() as temp_directory:
      test_profiler = profiler.CPUTimeProfiler(
          u'unittest', path=temp_directory)

      for _ in range(5):
        test_profiler.StartTiming(u'test_profile')
        time.sleep(0.01)
        test_profiler.StopTiming(u'test_profile')

      test_profiler.Write()


# Note that this test can be extremely slow with guppy version 0.1.9
# use version 0.1.10 or later.
@unittest.skipIf(not hpy, 'missing guppy.hpy')
class GuppyMemoryProfilerTest(shared_test_lib.BaseTestCase):
  """Tests for the guppy-based memory profiler."""

  def testGuppyMemoryProfiler(self):
    """Tests the Start, Sample and Stop functions."""
    self.assertTrue(profiler.GuppyMemoryProfiler.IsSupported())

    with shared_test_lib.TempDirectory() as temp_directory:
      test_profiler = profiler.GuppyMemoryProfiler(
          u'unittest', path=temp_directory)

      test_profiler.Start()

      for _ in range(5):
        test_profiler.Sample()
        time.sleep(0.01)

      test_profiler.Stop()


if __name__ == '__main__':
  unittest.main()
