#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for the BagMRU Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import bagmru
from plaso.parsers.winreg_plugins import test_lib
from plaso.winreg import test_lib as winreg_test_lib


class TestBagMRUPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the BagMRU plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = bagmru.BagMRUPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['NTUSER.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU')
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 15)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2009-08-04 15:19:16.997750')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value 0]: '
        u'Shell item list: [My Computer]').format(key_path)

    expected_msg_short = (
        u'[{0:s}] Index: 1 [MRU Value 0]: Shel...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[1]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2009-08-04 15:19:10.669625')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}\\0] '
        u'Index: 1 [MRU Value 0]: '
        u'Shell item list: [My Computer, C:\\]').format(key_path)

    expected_msg_short = (
        u'[{0:s}\\0] Index: 1 [MRU Value 0]: Sh...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[14]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2009-08-04 15:19:16.997750')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    # The winreg_formatter will add a space after the key path even when there
    # is not text.
    expected_msg = u'[{0:s}\\0\\0\\0\\0\\0] '.format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
