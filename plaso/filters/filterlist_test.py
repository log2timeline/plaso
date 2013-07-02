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
"""Tests for the PFilters filter."""
import os
import logging
import tempfile
import unittest

from plaso.filters import filterlist
from plaso.filters import test_helper


class ObjectFilterTest(test_helper.FilterTestHelper):
  """Tests for the ObjectFilterList filter."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.test_filter = filterlist.ObjectFilterList()

  def testFilterFail(self):
    """Run few tests that should not be a proper filter."""
    self.TestFail('SELECT stuff FROM machine WHERE conditions are met')
    self.TestFail('/tmp/file_that_most_likely_does_not_exist')
    self.TestFail('some random stuff that is destined to fail')
    self.TestFail('some_stuff is "random" and other_stuff ')
    self.TestFail('some_stuff is "random" and other_stuff is not "random"')

  def CreateFileAndTest(self, content):
    """Creates a file and then runs the test."""
    name = ''
    with tempfile.NamedTemporaryFile(delete=False) as fh:
      name = fh.name
      fh.write(content)

    self.TestTrue(name)

    try:
      os.remove(name)
    except (OSError, IOError) as e:
      logging.warning(
          u'Unable to remove temporary file: %s due to: %s', name, e)

  def testFilterApprove(self):
    one_rule = """
Again_Dude:
  description: Heavy artillery caught on fire
  case_nr: 62345
  analysts: [anonymous]
  urls: [cnn.com,microsoft.com]
  filter: message contains "dude where is my car"
    """
    self.CreateFileAndTest(one_rule)

    collection = """
Rule_Dude:
    description: This is the very case I talk about, a lot
    case_nr: 1235
    analysts: [dude, jack, horn]
    urls: [mbl.is,visir.is]
    filter: date > "2012-01-01 10:54:13" and parser not contains "evtx"

Again_Dude:
  description: Heavy artillery caught on fire
  case_nr: 62345
  analysts: [smith, perry, john]
  urls: [cnn.com,microsoft.com]
  filter: message contains "dude where is my car"

Third_Rule_Of_Thumb:
    description: Another ticket for another day.
    case_nr: 234
    analysts: [joe]
    urls: [mbl.is,symantec.com/whereevillies,virustotal.com/myhash]
    filter: evil_bit is 1
    """
    self.CreateFileAndTest(collection)


if __name__ == '__main__':
  unittest.main()
