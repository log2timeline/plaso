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
"""Tests for the Google Chrome History database plugin."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import chrome as chrome_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers.sqlite_plugins import chrome
from plaso.parsers.sqlite_plugins import test_lib


class ChromeHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome History database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._plugin = chrome.ChromeHistoryPlugin(pre_obj)

  def testProcess(self):
    """Tests the Process function on a Chrome History database file."""
    test_file = self._GetTestFilePath(['History'])
    event_generator = self._ParseDatabaseFileWithPlugin(self._plugin, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # The History file contains 71 events (69 page visits, 1 file downloads).
    self.assertEquals(len(event_objects), 71)

    # Check the first page visited entry.
    event_object = event_objects[0]

    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.PAGE_VISITED)

    # date -u -d"2011-04-07 12:03:11.000000" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1302177791 * 1000000)

    expected_url = u'http://start.ubuntu.com/10.04/Google/'
    self.assertEquals(event_object.url, expected_url)

    expected_title = u'Ubuntu Start Page'
    self.assertEquals(event_object.title, expected_title)

    expected_msg = (
         u'{} ({}) [count: 0] Host: start.ubuntu.com '
         u'(URL not typed directly - no typed count)').format(
             expected_url, expected_title)
    expected_short = u'{} ({})'.format(expected_url, expected_title)

    self._TestGetMessageStrings(event_object, expected_msg, expected_short)

    # Check the first file downloaded entry.
    event_object = event_objects[69]

    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.FILE_DOWNLOADED)

    # date -u -d"2011-05-23 08:35:30.000000" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1306139730 * 1000000)

    expected_url = (
        u'http://fatloss4idiotsx.com/download/funcats/'
        u'funcats_scr.exe')
    self.assertEquals(event_object.url, expected_url)

    expected_full_path = u'/home/john/Downloads/funcats_scr.exe'
    self.assertEquals(event_object.full_path, expected_full_path)

    expected_msg = (
         u'{} ({}). Received: 1132155 bytes out of: 1132155 bytes.').format(
             expected_url, expected_full_path)
    expected_short = u'{} downloaded (1132155 bytes)'.format(expected_full_path)
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
