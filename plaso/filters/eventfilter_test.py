#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the EventObjectFilter filter."""
import unittest

from plaso.filters import test_helper
from plaso.filters import eventfilter


class EventObjectFilterTest(test_helper.FilterTestHelper):
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
