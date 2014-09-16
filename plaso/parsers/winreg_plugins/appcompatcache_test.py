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
"""Tests for the Application Compatibility Cache key Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import appcompatcache
from plaso.parsers.winreg_plugins import test_lib


class AppCompatCacheRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the AppCompatCache Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = appcompatcache.AppCompatCachePlugin()

  def testProcess(self):
    """Tests the Process function."""
    knowledge_base_values = {'current_control_set': u'ControlSet001'}
    test_file = self._GetTestFilePath(['SYSTEM'])
    key_path = u'\\ControlSet001\\Control\\Session Manager\\AppCompatCache'
    winreg_key = self._GetKeyFromFile(test_file, key_path)

    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 330)

    event_object = event_objects[9]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-04-04 01:46:37.932964')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEquals(event_object.keyname, key_path)
    expected_msg = (
        u'[{0:s}] Cached entry: 10 Path: '
        u'\\??\\C:\\Windows\\PSEXESVC.EXE'.format(event_object.keyname))

    expected_msg_short = (
        u'Path: \\??\\C:\\Windows\\PSEXESVC.EXE')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
