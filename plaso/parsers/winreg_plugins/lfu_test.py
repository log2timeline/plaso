#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Tests for the Less Frequently Used (LFU) Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import lfu
from plaso.parsers.winreg_plugins import test_lib
from plaso.winreg import cache
from plaso.winreg import test_lib as winreg_test_lib


class TestBootExecutePlugin(test_lib.RegistryPluginTestCase):
  """Tests for the LFU BootExecute Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry_cache = cache.WinRegistryCache()
    registry_cache.attributes['current_control_set'] = 'ControlSet001'
    self._plugin = lfu.BootExecutePlugin(reg_cache=registry_cache)

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\ControlSet001\\Control\\Session Manager'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        'BootExecute', 'autocheck autochk *\x00'.encode('utf_16_le'), 7, 123))
    values.append(winreg_test_lib.TestRegValue(
        'CriticalSectionTimeout', '2592000'.encode('utf_16_le'), 1, 153))
    values.append(winreg_test_lib.TestRegValue(
        'ExcludeFromKnownDlls', '\x00'.encode('utf_16_le'), 7, 163))
    values.append(winreg_test_lib.TestRegValue(
        'GlobalFlag', '0'.encode('utf_16_le'), 1, 173))
    values.append(winreg_test_lib.TestRegValue(
        'HeapDeCommitFreeBlockThreshold', '0'.encode('utf_16_le'), 1, 183))
    values.append(winreg_test_lib.TestRegValue(
        'HeapDeCommitTotalFreeThreshold', '0'.encode('utf_16_le'), 1, 203))
    values.append(winreg_test_lib.TestRegValue(
        'HeapSegmentCommit', '0'.encode('utf_16_le'), 1, 213))
    values.append(winreg_test_lib.TestRegValue(
        'HeapSegmentReserve', '0'.encode('utf_16_le'), 1, 223))
    values.append(winreg_test_lib.TestRegValue(
        'NumberOfInitialSessions', '2'.encode('utf_16_le'), 1, 243))

    timestamp = timelib_test.CopyStringToTimestamp('2012-08-31 20:45:29')
    winreg_key = winreg_test_lib.TestRegKey(key_path, timestamp, values, 153)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 2)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-08-31 20:45:29')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'[{0:s}] BootExecute: autocheck autochk *').format(key_path)

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[1]

    expected_msg = (
        u'[{0:s}] '
        u'CriticalSectionTimeout: 2592000 '
        u'ExcludeFromKnownDlls: [] '
        u'GlobalFlag: 0 '
        u'HeapDeCommitFreeBlockThreshold: 0 '
        u'HeapDeCommitTotalFreeThreshold: 0 '
        u'HeapSegmentCommit: 0 '
        u'HeapSegmentReserve: 0 '
        u'NumberOfInitialSessions: 2').format(key_path)

    expected_msg_short = (
        u'[{0:s}] CriticalSectionTimeout: 2592000 Excl...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class TestBootVerificationRegistry(test_lib.RegistryPluginTestCase):
  """Tests for the LFU BootVerification Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry_cache = cache.WinRegistryCache()
    registry_cache.attributes['current_control_set'] = 'ControlSet001'
    self._plugin = lfu.BootVerificationPlugin(reg_cache=registry_cache)

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\ControlSet001\\Control\\BootVerificationProgram'
    values = []

    values.append(winreg_test_lib.TestRegValue(
        'ImagePath',
        'C:\\WINDOWS\\system32\\googleupdater.exe'.encode('utf_16_le'), 1,
        123))

    timestamp = timelib_test.CopyStringToTimestamp('2012-08-31 20:45:29')
    winreg_key = winreg_test_lib.TestRegKey(key_path, timestamp, values, 153)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-08-31 20:45:29')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}] '
        u'ImagePath: C:\\WINDOWS\\system32\\googleupdater.exe').format(
            key_path)

    expected_msg_short = (
        u'[{0:s}] ImagePath: C:\\WINDOWS\\system...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
