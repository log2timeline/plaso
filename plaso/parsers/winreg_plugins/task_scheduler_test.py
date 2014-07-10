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
"""Tests for the Task Scheduler Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import task_scheduler
from plaso.parsers.winreg_plugins import test_lib


class TaskCachePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Task Cache key Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = task_scheduler.TaskCachePlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['SOFTWARE-RunTests'])
    key_path = (
        u'\\Microsoft\\Windows NT\\CurrentVersion\\Schedule\\TaskCache')
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 174)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2009-07-14 04:53:25.811618')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'Task: SynchronizeTime'
    expected_value = u'[ID: {044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}]'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_msg = u'[{0:s}] {1:s}: {2:s}'.format(
          key_path, regvalue_identifier, expected_value)

    expected_msg_short = u'[{0:s}] Task: SynchronizeTi...'.format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[1]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2009-07-14 05:08:50.811626')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'Task: SynchronizeTime'

    expected_msg = (
        u'Task: SynchronizeTime '
        u'[Identifier: {044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}]')

    expected_msg_short = (
        u'Task: SynchronizeTime')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
