#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Headphone Audio Levels SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_headphone_audio_levels
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthHeadphoneAudioPluginGoldenTest(test_lib.SQLitePluginTestCase):
  """Golden-value tests for the iOS Health Headphone Audio Levels plugin."""

  def testProcess(self):
    """Tests the Process function on a healthdb_secure.sqlite file."""
    plugin = ios_health_headphone_audio_levels.IOSHealthHeadphoneAudioPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['healthdb_secure.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertGreater(number_of_event_data, 0)

    self.assertEqual(
        storage_writer.GetNumberOfAttributeContainers('extraction_warning'), 0)
    self.assertEqual(
        storage_writer.GetNumberOfAttributeContainers('recovery_warning'), 0)

    expected_event_values = {
        'bundle_name': 'com.apple.Music',
        'data_id': 12345,
        'data_type': 'ios:health:headphone_audio_levels',
        'date_time': '2023-10-27T10:00:00+00:00',
        'decibels': 65.5,
        'device_manufacturer': 'Apple Inc.',
        'device_model': 'AirPods Pro',
        'device_name': 'My AirPods',
        'end_date_str': '2023-10-27T10:05:00+00:00',
        'local_identifier': 'A1B2C3D4-E5F6',
        'start_date_str': '2023-10-27T10:00:00+00:00',
        'total_time_duration': '00:05:00'}

    matched_index = None
    for i in range(number_of_event_data):
      event_data = storage_writer.GetAttributeContainerByIndex('event_data', i)
      if (getattr(event_data, 'data_id', None) == 12345 and
          getattr(event_data, 'decibels', None) == 65.5):
        matched_index = i
        break

    msg = 'Golden headphone audio event not found in parsed results.'
    self.assertIsNotNone(matched_index, msg=msg)

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', matched_index)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
  