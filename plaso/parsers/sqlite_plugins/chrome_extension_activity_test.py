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
"""Tests for the Google Chrome extension activity database plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import chrome_extension_activity as chrome_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import chrome_extension_activity
from plaso.parsers.sqlite_plugins import test_lib


class ChromeExtensionActivityPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome extension activity database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = chrome_extension_activity.ChromeExtensionActivityPlugin()

  def testProcess(self):
    """Tests the Process function on a Chrome extension activity database."""
    test_file = self._GetTestFilePath(['Extension Activity'])
    cache = sqlite.SQLiteCache()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file, cache)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 56)

    event_object = event_objects[0]

    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.UNKNOWN)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-11-25 21:08:23.698737')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_extension_id = u'ognampngfcbddbfemdapefohjiobgbdl'
    self.assertEquals(event_object.extension_id, expected_extension_id)

    self.assertEquals(event_object.action_type, 1)
    self.assertEquals(event_object.activity_id, 48)
    self.assertEquals(event_object.api_name, u'browserAction.onClicked')

    expected_msg = (
        u'Chrome extension: ognampngfcbddbfemdapefohjiobgbdl '
        u'Action type: 1 '
        u'Activity identifier: 48 '
        u'API name: browserAction.onClicked')
    expected_short = (
        u'ognampngfcbddbfemdapefohjiobgbdl browserAction.onClicked')

    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
