#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android SMS plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_native_downloads

from tests.parsers.sqlite_plugins import test_lib

class AndroidNativeDownloadsTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android native downloads database plugin."""

  def testProcess(self):
      """Test the Process function on an Android native downloads database (downloads.db) file."""
      plugin = android_native_downloads.AndroidNativeDownloadsPlugin()
      storage_writer = self._ParseDatabaseFileWithPlugin(['downloads.db'], plugin)

      # The Native Downloads database file contains 11 events.
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
          'lastmod': '2022-11-12T15:32:28.279+00:00',
          'id': 46,
          'uri': 'https://cdn.discordapp.com/attachments/622810296226152474/1041012392089370735/IMG_1953.jpg',
          'mimetype': 'image/jpeg',
          'total_bytes': 2149749,
          'current_bytes': 2149749,
          'status': 200,
          'saved_to': '/storage/emulated/0/Download/IMG_1953.jpg',
          'deleted': 0,
          'notification_package': 'com.discord',
          'title': 'IMG_1953.jpg',
          'media_provider_uri': 'content://media/external_primary/images/media/1000000486',
          'error_msg': None,
          'is_visible_in_downloads_ui': 1,
          'destination': 4,
          'ui_visibility': 1,
          'e_tag': '"932f5b7818a3c0c1284cda69b6d7ea30"',
          'description': '',
      }

      event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
      self.CheckEventData(event_data, expected_event_values)

  if __name__ == '__main__':
      unittest.main()
