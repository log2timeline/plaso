#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
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
"""This file contains helper function and classes for filters."""
import unittest

from plaso.lib import errors


class FilterTestHelper(unittest.TestCase):
  """A simple class that provides helper functions for testing filters."""

  def setUp(self):
    """This should be overwritten."""
    self.test_filter = None

  def TestTrue(self, query):
    """A quick test that should return a valid filter."""
    if not self.test_filter:
      self.assertTrue(False)

    try:
      self.test_filter.CompileFilter(query)
      # And a success.
      self.assertTrue(True)
    except errors.WrongPlugin:
      # Let the test fail.
      self.assertTrue(False)

  def TestFail(self, query):
    """A quick failure test with a filter."""
    if not self.test_filter:
      self.assertTrue(False)

    with self.assertRaises(errors.WrongPlugin):
      self.test_filter.CompileFilter(query)

