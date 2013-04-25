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
"""Tests for the DynamicFilter filter."""
import unittest

from plaso.filters import dynamic_filter
from plaso.filters import test_helper


class DynamicFilterTest(test_helper.FilterTestHelper):
  """Tests for the DynamicFilter filter."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.test_filter = dynamic_filter.DynamicFilter()

  def testFilterFail(self):
    """Run few tests that should not be a proper filter."""
    self.TestFail('/tmp/file_that_most_likely_does_not_exist')
    self.TestFail('some random stuff that is destined to fail')
    self.TestFail('some_stuff is "random" and other_stuff ')
    self.TestFail('some_stuff is "random" and other_stuff is not "random"')
    self.TestFail('SELECT stuff FROM machine WHERE conditions are met')
    self.TestFail('SELECT field_a, field_b WHERE ')

  def testFilterApprove(self):
    self.TestTrue('SELECT stuff FROM machine WHERE some_stuff is "random"')
    self.TestTrue('SELECT field_a, field_b, field_c')
    self.TestTrue('SELECT field_a, field_b, field_c WHERE date > "2012"')
    self.TestTrue((
        'SELECT parser, date, time WHERE some_stuff is "random" and '
        'date < "2021-02-14 14:51:23"'))

  def testFilterFields(self):
    query = 'SELECT stuff FROM machine WHERE some_stuff is "random"'
    self.test_filter.CompileFilter(query)
    self.assertEquals(['stuff'], self.test_filter.fields)

    query = 'SELECT stuff, a, b, date FROM machine WHERE some_stuff is "random"'
    self.test_filter.CompileFilter(query)
    self.assertEquals(['stuff', 'a', 'b', 'date'], self.test_filter.fields)

    query = 'SELECT date, message, zone, hostname WHERE some_stuff is "random"'
    self.test_filter.CompileFilter(query)
    self.assertEquals(['date', 'message', 'zone', 'hostname'],
                      self.test_filter.fields)


if __name__ == '__main__':
  unittest.main()
