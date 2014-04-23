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
"""Tests for the Google Drive database plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import gdrive as gdrive_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers.sqlite_plugins import gdrive
from plaso.parsers.sqlite_plugins import interface
from plaso.parsers.sqlite_plugins import test_lib


class GoogleDrivePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Drive database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._plugin = gdrive.GoogleDrivePlugin(pre_obj)

  def testProcess(self):
    """Tests the Process function on a Google Drive database file."""
    test_file = self._GetTestFilePath(['snapshot.db'])
    cache = interface.SQLiteCache()
    event_generator = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file, cache=cache)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 30)

    # Let's verify that we've got the correct balance of cloud and local
    # entry events.
    #   10 files mounting to:
    #     20 Cloud Entries (two timestamps per file).
    #     10 Local Entries (one timestamp per file).
    local_entries = []
    cloud_entries = []
    for event_object in event_objects:
      if event_object.data_type == 'gdrive:snapshot:local_entry':
        local_entries.append(event_object)
      else:
        cloud_entries.append(event_object)
    self.assertEquals(len(local_entries), 10)
    self.assertEquals(len(cloud_entries), 20)

    # Test one local and one cloud entry.
    event_object = local_entries[5]

    file_path = (
        u'%local_sync_root%/Top Secret/Enn meiri '
        u'leyndarm\xe1l/S\xfdnileiki - \xd6rverpi.gdoc')
    self.assertEquals(event_object.path, file_path)

    expected_msg = u'File Path: {} Size: 184'.format(file_path)

    self._TestGetMessageStrings(event_object, expected_msg, file_path)

    # date -u -d "2014-01-28T00:11:25+00:00" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1390867885000000)

    event_object = cloud_entries[16]

    self.assertEquals(event_object.document_type, u'DOCUMENT')
    self.assertEquals(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.MODIFICATION_TIME)
    self.assertEquals(event_object.url, (
        u'https://docs.google.com/document/d/'
        u'1ypXwXhQWliiMSQN9S5M0K6Wh39XF4Uz4GmY-njMf-Z0/edit?usp=docslist_api'))

    expected_msg = (
        u'File Path: /Almenningur/Saklausa hli\xf0in [Private] Size: 0 URL: '
        u'https://docs.google.com/document/d/'
        u'1ypXwXhQWliiMSQN9S5M0K6Wh39XF4Uz4GmY-njMf-Z0/edit?usp=docslist_api '
        u'Type: DOCUMENT')
    expected_short = u'/Almenningur/Saklausa hli\xf0in'

    self._TestGetMessageStrings(event_object, expected_msg, expected_short)

    # date -u -d "2014-01-28T00:12:27+00:00" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1390867947000000)


if __name__ == '__main__':
  unittest.main()
