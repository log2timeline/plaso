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
"""This file contains a test for MRU registry parsing in Plaso."""
import unittest

from plaso.lib import eventdata
from plaso.registry import mru
from plaso.registry import test_lib


class TestMRURegistry(unittest.TestCase):
  """The unit test for MRU registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue('MRUList', 'acb'.encode('utf_16_le'),
                                        1, 123))
    values.append(test_lib.TestRegValue(
        'a', 'Some random text here'.encode('utf_16_le'), 1, 1892))
    values.append(test_lib.TestRegValue(
        'b', 'c:/evil.exe'.encode('utf_16_le'), 3, 612))
    values.append(test_lib.TestRegValue(
        'c', 'C:/looks_legit.exe'.encode('utf_16_le'), 1, 1001))

    self.regkey = test_lib.TestRegKey(
        '\\Microsoft\\Some Windows\\InterestingApp\\MRU', 1346145829002031,
        values, 1456)

  def testMRU(self):
    """Run a simple test against a mocked MRU list."""
    plugin = mru.MRUPlugin(None)
    generator = plugin.Process(self.regkey)
    self.assertTrue(generator)
    entries = list(generator)

    line1 = ('[\\Microsoft\\Some Windows\\InterestingApp\\MRU] MRUList Entry '
             '1: Some random text here')
    line2 = ('[\\Microsoft\\Some Windows\\InterestingApp\\MRU] MRUList Entry '
             '2: C:/looks_legit.exe')
    line3 = ('[\\Microsoft\\Some Windows\\InterestingApp\\MRU] MRUList Entry '
             '3: c:/evil.exe')

    self.assertEquals(len(entries), 3)
    self.assertEquals(entries[0].timestamp, 1346145829002031)
    self.assertEquals(entries[1].timestamp, 0)
    self.assertEquals(entries[2].timestamp, 0)

    msg1, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    msg2, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    msg3, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[2])

    self.assertEquals(msg1, line1)
    self.assertEquals(msg2, line2)
    self.assertEquals(msg3, line3)


if __name__ == '__main__':
  unittest.main()
