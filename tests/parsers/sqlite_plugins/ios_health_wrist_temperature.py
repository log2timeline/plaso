#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Wrist Temperature SQLite database plugin."""

import math
import unittest

from plaso.parsers.sqlite_plugins import ios_health_wrist_temperature
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWristTemperatureTest(test_lib.SQLitePluginTestCase):
  """Tests for iOS Health Wrist Temperature SQLite database plugin."""

  def testProcess(self):
    """Test the plugin's Process function on a test database."""
    plugin = ios_health_wrist_temperature.IOSHealthWristTemperaturePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['healthdb_secure.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertGreater(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_recovery_warnings, 0)

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)

    self.assertIsNotNone(event_data.start_time_str)
    self.assertTrue(event_data.start_time_str.startswith('2020-04-12T18:00:00'))

    self.assertIsNotNone(event_data.end_time_str)
    self.assertTrue(event_data.end_time_str.startswith('2020-04-12T19:00:00'))

    self.assertIsNotNone(event_data.date_added_str)
    self.assertTrue(event_data.date_added_str.startswith('2020-04-12T18:58:43'))

    self.assertIsNotNone(event_data.date_time)
    self.assertEqual(event_data.date_time, event_data.start_time)

    expected_event_values = {
        'device_manufacturer': 'Apple Inc.',
        'device_model': 'Watch',
        'device_name': 'Apple Watch',
        'hardware_version': 'Watch4,3',
        'software_version': '6.1.3',
        'source': 'This Is’s Apple Watch',
        'wrist_temperature_c': 36.6}

    self.CheckEventData(event_data, expected_event_values)

    wrist_temp_f = getattr(event_data, 'wrist_temperature_f', None)
    if wrist_temp_f is not None:
      expected_f = 36.6 * 1.8 + 32
      self.assertTrue(math.isclose(wrist_temp_f, expected_f, rel_tol=1e-6))


if __name__ == '__main__':
  unittest.main()
  