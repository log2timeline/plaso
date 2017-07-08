#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Drive database plugin."""

import unittest

from plaso.formatters import gdrive  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import gdrive

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class GoogleDrivePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Drive database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'snapshot.db'])
  def testProcess(self):
    """Tests the Process function on a Google Drive database file."""
    plugin = gdrive.GoogleDrivePlugin()
    cache = sqlite.SQLiteCache()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'snapshot.db'], plugin, cache=cache)

    self.assertEqual(storage_writer.number_of_events, 30)

    # Let's verify that we've got the correct balance of cloud and local
    # entry events.
    #   10 files mounting to:
    #     20 Cloud Entries (two timestamps per entry).
    #     10 Local Entries (one timestamp per entry).
    local_entries = []
    cloud_entries = []
    for event in storage_writer.GetEvents():
      if event.data_type == u'gdrive:snapshot:local_entry':
        local_entries.append(event)
      else:
        cloud_entries.append(event)

    self.assertEqual(len(local_entries), 10)
    self.assertEqual(len(cloud_entries), 20)

    # Test one local and one cloud entry.
    event = local_entries[5]

    file_path = (
        u'%local_sync_root%/Top Secret/Enn meiri '
        u'leyndarmál/Sýnileiki - Örverpi.gdoc')
    self.assertEqual(event.path, file_path)

    expected_message = u'File Path: {0:s} Size: 184'.format(file_path)

    self._TestGetMessageStrings(event, expected_message, file_path)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-28 00:11:25')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = cloud_entries[16]

    self.assertEqual(event.document_type, 6)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    expected_url = (
        u'https://docs.google.com/document/d/'
        u'1ypXwXhQWliiMSQN9S5M0K6Wh39XF4Uz4GmY-njMf-Z0/edit?usp=docslist_api')
    self.assertEqual(event.url, expected_url)

    expected_message = (
        u'File Path: /Almenningur/Saklausa hliðin '
        u'[Private] '
        u'Size: 0 '
        u'URL: {0:s} '
        u'Type: DOCUMENT').format(expected_url)
    expected_short_message = u'/Almenningur/Saklausa hliðin'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-28 00:12:27')
    self.assertEqual(event.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
