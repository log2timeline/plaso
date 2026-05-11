#!/usr/bin/env python3
"""Tests for the Android native downloads database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_native_downloads

from tests.parsers.sqlite_plugins import test_lib

class AndroidNativeDownloadsTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android native downloads database plugin."""

  def testProcess(self):
    """Test the Process function on an Android downloads.db file."""
    plugin = android_native_downloads.AndroidNativeDownloadsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['downloads.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 11)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'current_bytes': 2149749,
        'deleted': 0,
        'description': None,
        'destination': 4,
        'error_msg': None,
        'e_tag': '"932f5b7818a3c0c1284cda69b6d7ea30"',
        'identifier': 46,
        'is_visible_in_downloads_ui': 1,
        'media_provider_uri': (
            'content://media/external_primary/images/media/1000000486'),
        'mime_type': 'image/jpeg',
        'modification_time': '2022-11-12T15:32:28.279+00:00',
        'notification_package': 'com.discord',
        'saved_to': '/storage/emulated/0/Download/IMG_1953.jpg',
        'status': 200,
        'title': 'IMG_1953.jpg',
        'total_bytes': 2149749,
        'ui_visibility': 1,
        'uri': (
            'https://cdn.discordapp.com/attachments/'
            '622810296226152474/1041012392089370735/IMG_1953.jpg')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
