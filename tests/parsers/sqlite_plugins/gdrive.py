#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Drive database plugin."""

import unittest

from plaso.formatters import gdrive as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import gdrive

from tests.parsers.sqlite_plugins import test_lib


class GoogleDrivePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Drive database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = gdrive.GoogleDrivePlugin()

  def testProcess(self):
    """Tests the Process function on a Google Drive database file."""
    test_file = self._GetTestFilePath([u'snapshot.db'])
    cache = sqlite.SQLiteCache()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file, cache=cache)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 30)

    # Let's verify that we've got the correct balance of cloud and local
    # entry events.
    #   10 files mounting to:
    #     20 Cloud Entries (two timestamps per entry).
    #     10 Local Entries (one timestamp per entry).
    local_entries = []
    cloud_entries = []
    for event_object in event_objects:
      if event_object.data_type == u'gdrive:snapshot:local_entry':
        local_entries.append(event_object)
      else:
        cloud_entries.append(event_object)

    self.assertEqual(len(local_entries), 10)
    self.assertEqual(len(cloud_entries), 20)

    # Test one local and one cloud entry.
    event_object = local_entries[5]

    file_path = (
        u'%local_sync_root%/Top Secret/Enn meiri '
        u'leyndarmál/Sýnileiki - Örverpi.gdoc')
    self.assertEqual(event_object.path, file_path)

    expected_msg = u'File Path: {0:s} Size: 184'.format(file_path)

    self._TestGetMessageStrings(event_object, expected_msg, file_path)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-28 00:11:25')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = cloud_entries[16]

    self.assertEqual(event_object.document_type, u'DOCUMENT')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    expected_url = (
        u'https://docs.google.com/document/d/'
        u'1ypXwXhQWliiMSQN9S5M0K6Wh39XF4Uz4GmY-njMf-Z0/edit?usp=docslist_api')
    self.assertEqual(event_object.url, expected_url)

    expected_msg = (
        u'File Path: /Almenningur/Saklausa hliðin '
        u'[Private] '
        u'Size: 0 '
        u'URL: {0:s} '
        u'Type: DOCUMENT').format(expected_url)
    expected_msg_short = u'/Almenningur/Saklausa hliðin'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-28 00:12:27')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
