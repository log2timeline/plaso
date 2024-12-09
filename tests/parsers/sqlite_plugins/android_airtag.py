#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android AirGuard AirTag Tracker plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_airtag

from tests.parsers.sqlite_plugins import test_lib


class AirTagPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android AirGuard AirTag Tracker database plugin."""

  def testProcess(self):
    """Test the Process function on an Android attd_db file."""
    plugin = android_airtag.AirTagPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['attd_db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 868)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'device_address': 'F2:21:EF:BF:DE:58',
        'data_type': 'android:airtag:event',
        'rssi': -97,
        'latitude': -97.7381371,
        'longitude': 30.2654229,
        'device_name': None,
        'first_discovery': '2022-08-16T18:26:18.159+00:00',
        'last_seen': '2022-08-16T18:26:18.159+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
  
