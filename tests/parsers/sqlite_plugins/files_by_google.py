#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Files by Google messages plugin."""

import unittest

from plaso.parsers.sqlite_plugins import files_by_google

from tests.parsers.sqlite_plugins import test_lib


class FilesByGooglePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Files by Google message database plugin."""

  def testProcess(self):
    """Test the Process function on a Files by Google file."""
    plugin = files_by_google.FilesByGooglePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['files_master_database'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 171)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'date_modified' : '2021-08-10T23:22:30.000+00:00',
        'root_path' : '/storage/emulated/0',
        'root_relative_path' : 'Download/MEGA Downloads/2021-08-10 19.22.30.jpg',
        'file_name' : '2021-08-10 19.22.30.jpg',
        'file_size' : 729513,
        'mime_type' : 'image/jpeg',
        'media_type' : 1,
        'uri' : 'content://media/external/file/1000000589',
        'is_hidden' : 0,
        'title' : '2021-08-10 19.22.30',
        'parent_folder' : 'MEGA Downloads'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
