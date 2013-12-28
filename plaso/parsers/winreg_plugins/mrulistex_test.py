#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a test for MRUx registry parsing in Plaso."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import eventdata
from plaso.parsers.winreg_plugins import mrulistex
from plaso.winreg import test_lib


class TestMRUxRegistry(unittest.TestCase):
  """The unit test for MRU registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    # The order is: 201
    values.append(test_lib.TestRegValue(
        'MRUListEx', '\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00',
        3, 123))
    values.append(test_lib.TestRegValue(
        '0', 'Some random text here'.encode('utf_16_le'), 1, 1892))
    values.append(test_lib.TestRegValue(
        '1', 'c:/evil.exe'.encode('utf_16_le'), 3, 612))
    values.append(test_lib.TestRegValue(
        '2', 'C:/looks_legit.exe'.encode('utf_16_le'), 1, 1001))

    self.regkey = test_lib.TestRegKey(
        '\\Microsoft\\Some Windows\\InterestingApp\\MRUlist', 1346145829002031,
        values, 1456)

  def testMRUX(self):
    """Test the MRUexPlugin."""
    plugin = mrulistex.MRUexPlugin(None, None, None)
    entries = list(plugin.Process(self.regkey))

    line = ('[\\Microsoft\\Some Windows\\InterestingApp\\MRUlist] '
            'Index: 1 [MRU Value 2]: C:/looks_legit.exe '
            'Index: 2 [MRU Value 0]: Some random text here '
            'Index: 3 [MRU Value 1]: c:/evil.exe')

    self.assertEquals(len(entries), 1)
    event_object = entries[0]
    self.assertEquals(event_object.timestamp, 1346145829002031)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event_object)

    self.assertEquals(msg, line)


if __name__ == '__main__':
  unittest.main()
