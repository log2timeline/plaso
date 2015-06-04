#!/usr/bin/python
# -*- coding: utf-8 -*-
import unittest

from plaso.filters import eventfilter

from tests.filters import test_lib


class EventObjectFilterTest(test_lib.FilterTestHelper):
  """Tests for the EventObjectFilter filter."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.test_filter = eventfilter.EventObjectFilter()

  def testFilterFail(self):
    """Run few tests that should not be a proper filter."""
    self.TestFail('SELECT stuff FROM machine WHERE conditions are met')
    self.TestFail('/tmp/file_that_most_likely_does_not_exist')
    self.TestFail('some random stuff that is destined to fail')
    self.TestFail('some_stuff is "random" and other_stuff ')

  def testFilterApprove(self):
    self.TestTrue('some_stuff is "random" and other_stuff is not "random"')


if __name__ == '__main__':
  unittest.main()
