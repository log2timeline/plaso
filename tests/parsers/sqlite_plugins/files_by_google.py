#!/usr/bin/env python3
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
        'file_name': 'PXL_20220816_213228168.MP.jpg',
        'file_size': 5274656,
        'is_hidden': 0,
        'media_type': 1,
        'mime_type': 'image/jpeg',
        'modification_time': '2022-08-16T21:32:31.000+00:00',
        'parent_folder': 'Camera',
        'root_path': '/storage/emulated/0',
        'root_relative_path': 'DCIM/Camera/PXL_20220816_213228168.MP.jpg',
        'title': 'PXL_20220816_213228168.MP',
        'uri': 'content://media/external/file/1000000019'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
