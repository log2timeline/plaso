#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Source Devices SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_source_devices
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthSourceDevicesTest(test_lib.SQLitePluginTestCase):
  """Tests for iOS Health Source Devices SQLite database plugin."""

  def testProcess(self):
    """Test the Process function for source devices."""
    plugin = ios_health_source_devices.IOSHealthSourceDevicesPlugin()

    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['healthdb.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertGreater(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_recovery_warnings, 0)

    expected_event_values = {
        'creation_date_str': '2020-03-27T18:57:39+00:00',
        'device_name': 'Apple Watch Series 4',
        'firmware': '5.1',
        'hardware': 'W4P12',
        'local_identifier': '1234ABCD5678EFG',
        'manufacturer': 'Apple',
        'model': 'Series 4',
        'software': 'WatchOS 6',
        'sync_provenance': 'iCloud'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.assertIsNotNone(event_data.date_time)
    self.assertEqual(
        event_data.creation_date_str,
        expected_event_values['creation_date_str'])

    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
