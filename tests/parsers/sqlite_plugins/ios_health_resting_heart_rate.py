#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Resting Heart Rate SQLite database plugin (golden)."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_resting_heart_rate
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthRestingHeartRatePluginGoldenTest(test_lib.SQLitePluginTestCase):
  """Golden-value tests for the iOS Health Resting Heart Rate SQLite plugin."""

  def testProcess(self):
    """Tests the Process function on a healthdb_secure.sqlite file."""
    plugin = ios_health_resting_heart_rate.IOSHealthRestingHeartRatePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['healthdb_secure.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertGreater(number_of_event_data, 0)

    self.assertEqual(storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning'), 0)
    self.assertEqual(storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning'), 0)

    expected_event_values = {
        'data_added_to_health_str': '2020-03-27T19:15:40+00:00',
        'data_type': 'ios:health:resting_heart_rate',
        'date_time': '2020-03-27T18:57:39+00:00',
        'end_date_str': '2020-03-27T19:15:39+00:00',
        'hardware': 'Watch4,3',
        'resting_heart_rate': 75,
        'source': "This Is's Apple Watch",
        'start_date_str': '2020-03-27T18:57:39+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    if not (getattr(event_data, 'resting_heart_rate', None) == 75 and
            getattr(event_data, 'hardware', None) == 'Watch4,3' and
            getattr(event_data, 'source', None) == "This Is's Apple Watch"):
      matched = None
      for i in range(number_of_event_data):
        ed = storage_writer.GetAttributeContainerByIndex('event_data', i)
        if (getattr(ed, 'resting_heart_rate', None) == 75 and
            getattr(ed, 'hardware', None) == 'Watch4,3' and
            getattr(ed, 'source', None) == "This Is's Apple Watch"):
          matched = ed
          break

      msg = 'Golden resting heart rate event not found.'
      self.assertIsNotNone(matched, msg=msg)
      event_data = matched

    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
