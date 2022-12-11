#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Dropbox sync_history database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import dropbox

from tests.parsers.sqlite_plugins import test_lib


class DropboxSyncHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Dropbox sync_history database plugin."""

  def testProcess(self):
    """Tests the Process function on a Dropbox sync_history database file."""
    plugin = dropbox.DropboxSyncDatabasePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['sync_history.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'dropbox:sync_history:entry',
        'direction': 'upload',
        'event_type': 'file',
        'file_event_type': 'add',
        'file_identifier': 'XXXXXXXXXXXAAAAAAAAAGg',
        'local_path': '/home/useraa/Dropbox/loc1/create_local.txt',
        'recorded_time': '2022-02-17T10:57:18+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
