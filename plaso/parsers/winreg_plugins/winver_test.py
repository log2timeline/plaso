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
"""Tests for the WinVer Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import winver
from plaso.winreg import test_lib as winreg_test_lib


class WinVerPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the WinVer Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = winver.WinVerPlugin()

  def testWinVer(self):
    """Test the WinVer plugin."""
    key_path = u'\\Microsoft\\Windows NT\\CurrentVersion'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        'ProductName', 'MyTestOS'.encode('utf_16_le'), 1, 123))
    values.append(winreg_test_lib.TestRegValue(
        'CSDBuildNumber', '5'.encode('utf_16_le'), 1, 1892))
    values.append(winreg_test_lib.TestRegValue(
        'RegisteredOwner', 'A Concerned Citizen'.encode('utf_16_le'), 1, 612))
    values.append(winreg_test_lib.TestRegValue(
        'InstallDate', '\x13\x1aAP', 3, 1001))

    winreg_key = winreg_test_lib.TestRegKey(
        key_path, 1346445929000000, values, 153)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-08-31 20:09:55')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    # Note that the double spaces here are intentional.
    expected_msg = (
        u'[{0:s}]  '
        u'Windows Version Information:  '
        u'Owner: A Concerned Citizen '
        u'Product name: MyTestOS sp: 5').format(key_path)

    expected_msg_short = (
        u'[{0:s}]  '
        u'Windows Version Information:  '
        u'Owner: ...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
