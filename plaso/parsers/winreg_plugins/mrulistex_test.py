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
"""Tests for the MRUListEx Windows Registry plugin."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.parsers.winreg_plugins import mrulistex
from plaso.parsers.winreg_plugins import test_lib
from plaso.winreg import test_lib as winreg_test_lib


class TestMRUListExPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the MRUListEx Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = mrulistex.MRUListExPlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\Microsoft\\Some Windows\\InterestingApp\\MRUlist'
    values = []

    # The order is: 201
    values.append(winreg_test_lib.TestRegValue(
        'MRUListEx', '\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00',
        3, 123))
    values.append(winreg_test_lib.TestRegValue(
        '0', 'Some random text here'.encode('utf_16_le'), 1, 1892))
    values.append(winreg_test_lib.TestRegValue(
        '1', 'c:/evil.exe'.encode('utf_16_le'), 3, 612))
    values.append(winreg_test_lib.TestRegValue(
        '2', 'C:/looks_legit.exe'.encode('utf_16_le'), 1, 1001))

    winreg_key = winreg_test_lib.TestRegKey(
        key_path, 1346145829002031, values, 1456)

    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]
    self.assertEquals(event_object.timestamp, 1346145829002031)

    expected_msg = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value 2]: C:/looks_legit.exe '
        u'Index: 2 [MRU Value 0]: Some random text here '
        u'Index: 3 [MRU Value 1]: c:/evil.exe').format(key_path)

    expected_msg_short = (
        u'[{0:s}] Index: 1 [MRU Value 2]: C:/l...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
