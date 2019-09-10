#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Drive database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import gdrive as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import gdrive

from tests.parsers.sqlite_plugins import test_lib


class GoogleDrivePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Drive database plugin."""

  def testProcess(self):
    """Tests the Process function on a Google Drive database file."""
    plugin = gdrive.GoogleDrivePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['snapshot.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 30)

    # Let's verify that we've got the correct balance of cloud and local
    # entry events.
    #   10 files mounting to:
    #     20 Cloud Entries (two timestamps per entry).
    #     10 Local Entries (one timestamp per entry).
    local_entries = []
    cloud_entries = []
    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      if event_data.data_type == 'gdrive:snapshot:local_entry':
        local_entries.append(event)
      else:
        cloud_entries.append(event)

    self.assertEqual(len(local_entries), 10)
    self.assertEqual(len(cloud_entries), 20)

    # Test one local and one cloud entry.
    event = local_entries[5]

    self.CheckTimestamp(event.timestamp, '2014-01-28 00:11:25.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    file_path = (
        '%local_sync_root%/Top Secret/Enn meiri '
        'leyndarmál/Sýnileiki - Örverpi.gdoc')
    self.assertEqual(event_data.path, file_path)

    expected_message = 'File Path: {0:s} Size: 184'.format(file_path)

    self._TestGetMessageStrings(
        event_data, expected_message, file_path)

    event = cloud_entries[16]

    self.CheckTimestamp(event.timestamp, '2014-01-28 00:12:27.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.document_type, 6)
    expected_url = (
        'https://docs.google.com/document/d/'
        '1ypXwXhQWliiMSQN9S5M0K6Wh39XF4Uz4GmY-njMf-Z0/edit?usp=docslist_api')
    self.assertEqual(event_data.url, expected_url)

    expected_message = (
        'File Path: /Almenningur/Saklausa hliðin '
        '[Private] '
        'Size: 0 '
        'URL: {0:s} '
        'Type: DOCUMENT').format(expected_url)
    expected_short_message = '/Almenningur/Saklausa hliðin'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
