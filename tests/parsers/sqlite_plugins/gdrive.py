#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Drive database plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import gdrive

from tests.parsers.sqlite_plugins import test_lib


class GoogleDrivePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Drive database plugin."""

  def testProcess(self):
    """Tests the Process function on a Google Drive database file."""
    plugin = gdrive.GoogleDrivePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['snapshot.db'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 30)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

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
    expected_event_values = {
        'data_type': 'gdrive:snapshot:local_entry',
        'date_time': '2014-01-28 00:11:25',
        'path': (
            '%local_sync_root%/Top Secret/Enn meiri '
            'leyndarmál/Sýnileiki - Örverpi.gdoc'),
        'size': 184}

    self.CheckEventValues(
        storage_writer, local_entries[5], expected_event_values)

    expected_event_values = {
        'data_type': 'gdrive:snapshot:cloud_entry',
        'date_time': '2014-01-28 00:12:27',
        'document_type': 6,
        'path': '/Almenningur/Saklausa hliðin',
        'size': 0,
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'url': (
            'https://docs.google.com/document/d/1ypXwXhQWliiMSQN9S5M0K6Wh39XF4U'
            'z4GmY-njMf-Z0/edit?usp=docslist_api')}

    self.CheckEventValues(
        storage_writer, cloud_entries[16], expected_event_values)


if __name__ == '__main__':
  unittest.main()
