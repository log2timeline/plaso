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
    test_file = self._GetTestFilePath([u'/cases/FSC632_Registry/SYSTEM'])
    key_path = u'\\ControlSet001\\Enum\\USB'
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 10)

    event_object = event_objects[3]

    expected_value = u'VID_0781&PID_5530'
    self._TestRegvalue(event_object, u'subkey_name', expected_value)
    self._TestRegvalue(event_object, u'vendor', u'VID_0781')
    self._TestRegvalue(event_object, u'product', u'PID_5530')

    expected_msg = (
        u'[\\ControlSet001\\Enum\\USB] '
        u'product: PID_5530 '
        u'serial: 20060572701DB7123952 '
        u'subkey_name: VID_0781&PID_5530 '
        u'vendor: VID_0781')

    # Match UTC timestamp.
    time = long(timelib_test.CopyStringToTimestamp(
        u'2014-09-30 03:11:35.591136'))
    self.assertEquals(event_object.timestamp, time)

    expected_msg_short = (
        u'[\\ControlSet001\\Enum\\USB] '
        u'product: PID_5530 '
        u'serial: 20060572701DB7123952 '
        u'subk...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
