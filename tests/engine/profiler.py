#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the profiler classes."""

import unittest

from plaso.engine import profiler


class CPUTimeProfilerTest(unittest.TestCase):
  """Tests for the parser profiler."""

  def testInitialization(self):
    """Tests the initialization."""
    test_profiler = profiler.CPUTimeProfiler(u'test')
    self.assertNotEqual(test_profiler, None)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
