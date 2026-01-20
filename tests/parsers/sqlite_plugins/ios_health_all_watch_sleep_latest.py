#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health - All Watch Sleep (iOS 17+) SQLite plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_all_watch_sleep_latest
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthAllWatchSleepLatestPluginGoldenTest(
    test_lib.SQLitePluginTestCase):
  """Golden-value tests for the iOS Health - All Watch Sleep (stages) plugin."""

  def testProcess(self):
    """Tests the Process function on a healthdb_secure.sqlite file."""
    plugin = (
        ios_health_all_watch_sleep_latest.IOSHealthAllWatchSleepLatestPlugin())
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
        'data_type': 'ios:health:all_watch_sleep_latest',
        'date_time': '2024-07-23T03:25:36+00:00',
        'end_date_str': '2024-07-23 03:44:36+00:00',
        'sleep_state_code': 3,
        'sleep_state_hms': '00:19:00',
        'start_date_str': '2024-07-23 03:25:36+00:00'}

    matched_index = None
    for i in range(number_of_event_data):
      event_data = storage_writer.GetAttributeContainerByIndex('event_data', i)
      if (getattr(event_data, 'start_date_str', None) ==
          expected_event_values['start_date_str'] and
          getattr(event_data, 'end_date_str', None) ==
          expected_event_values['end_date_str'] and
          getattr(event_data, 'sleep_state_code', None) ==
          expected_event_values['sleep_state_code'] and
          getattr(event_data, 'sleep_state_hms', None) ==
          expected_event_values['sleep_state_hms']):
        matched_index = i
        break

    msg = 'Golden iOS 17+ sleep stage event not found in parsed results.'
    self.assertIsNotNone(matched_index, msg=msg)

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', matched_index)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
  