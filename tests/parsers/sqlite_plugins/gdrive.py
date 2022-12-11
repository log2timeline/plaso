#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Drive database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import gdrive

from tests.parsers.sqlite_plugins import test_lib


class GoogleDrivePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Drive database plugin."""

  def testProcess(self):
    """Tests the Process function on a Google Drive database file."""
    plugin = gdrive.GoogleDrivePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['snapshot.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 20)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test a snapshot local entry.
    expected_event_values = {
        'data_type': 'gdrive:snapshot:local_entry',
        'modification_time': '2014-01-28T00:11:25+00:00',
        'path': (
            '%local_sync_root%/Top Secret/Enn meiri '
            'leyndarmál/Sýnileiki - Örverpi.gdoc'),
        'size': 184}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 15)
    self.CheckEventData(event_data, expected_event_values)

    # Test a snapshot cloud entry.
    expected_event_values = {
        'data_type': 'gdrive:snapshot:cloud_entry',
        'creation_time': '2014-01-28T00:12:26+00:00',
        'document_type': 6,
        'modification_time': '2014-01-28T00:12:27+00:00',
        'path': '/Almenningur/Saklausa hliðin',
        'size': 0,
        'url': (
            'https://docs.google.com/document/d/1ypXwXhQWliiMSQN9S5M0K6Wh39XF4U'
            'z4GmY-njMf-Z0/edit?usp=docslist_api')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
