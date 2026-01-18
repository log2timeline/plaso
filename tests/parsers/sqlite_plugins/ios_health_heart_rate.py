#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Heart Rate (pre-iOS 15) SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_heart_rate
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthHeartRatePluginGoldenTest(test_lib.SQLitePluginTestCase):
  """Golden-value tests for the iOS Health Heart Rate SQLite database plugin."""

  def testProcess(self):
    """Tests the Process function on a healthdb_secure.sqlite file."""
    plugin = ios_health_heart_rate.IOSHealthHeartRatePlugin()
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
        'added_date_str': '2021-01-01T12:05:00+00:00',
        'bpm': 72,
        'context': 'Sedentary',
        'data_type': 'ios:health:heart_rate',
        'device_name': 'Apple Watch',
        'end_date_str': '2021-01-01T12:00:01+00:00',
        'hardware': 'Watch6,1',
        'manufacturer': 'Apple Inc.',
        'software_version': '7.2',
        'source_name': 'Health',
        'start_date_str': '2021-01-01T12:00:00+00:00',
        'tz_name': 'Europe/London'}

    matched_index = None
    for i in range(number_of_event_data):
      event_data = storage_writer.GetAttributeContainerByIndex('event_data', i)
      if (getattr(event_data, 'bpm', None) == 72 and
          getattr(event_data, 'context', None) == 'Sedentary' and
          getattr(event_data, 'start_date_str', None) ==
          '2021-01-01T12:00:00+00:00'):
        matched_index = i
        break

    msg = 'Golden heart rate event not found in parsed results.'
    self.assertIsNotNone(matched_index, msg=msg)

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', matched_index)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
