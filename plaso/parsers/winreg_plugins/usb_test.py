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
"""Tests for the USB Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import event
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import usb


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class USBPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the USB Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = usb.USBPlugin()

  def testProcess(self):
    """Tests the Process function."""
    knowledge_base_values = {u'current_control_set': u'ControlSet001'}
    test_file = self._GetTestFilePath([u'SYSTEM'])
    key_path = u'\\ControlSet001\\Enum\\USB'
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 7)

    event_object = event_objects[3]

    expected_value = u'VID_0E0F&PID_0002'
    self._TestRegvalue(event_object, u'subkey_name', expected_value)
    self._TestRegvalue(event_object, u'vendor', u'VID_0E0F')
    self._TestRegvalue(event_object, u'product', u'PID_0002')

    expected_msg = (
        r'[\ControlSet001\Enum\USB] product: PID_0002 serial: 6&2ab01149&0&2 '
        r'subkey_name: VID_0E0F&PID_0002 vendor: VID_0E0F')

    # Match UTC timestamp.
    time = long(timelib_test.CopyStringToTimestamp(
        u'2012-04-07 10:31:37.625246'))
    self.assertEquals(event_object.timestamp, time)

    expected_msg_short = u'{0:s}...'.format(expected_msg[0:77])

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
