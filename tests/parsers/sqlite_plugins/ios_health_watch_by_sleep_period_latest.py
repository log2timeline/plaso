#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS Health Watch by Sleep Period Latest (iOS 17+) plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_watch_by_sleep_period_latest
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWatchBySleepPeriodLatestPluginTest(
    test_lib.SQLitePluginTestCase):
  """Tests for the iOS Health Watch by Sleep Period Latest plugin."""

  def testProcess(self):
    """Test overall plugin handling including parsing a real SQLite file."""
    plugin = (
        ios_health_watch_by_sleep_period_latest.
        IOSHealthWatchBySleepPeriodLatestPlugin())

    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['healthdb_secure.sqlite'], plugin)

    self.assertEqual(storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning'), 0)
    self.assertEqual(storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning'), 0)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertGreater(number_of_event_data, 0)

    expected_event_values = {
        'awake_duration_hms': '00:01:00',
        'awake_percent': 0.24,
        'core_duration_hms': '03:28:00',
        'core_percent': 50.73,
        'data_type': 'ios:health:watch_by_sleep_period_latest',
        'deep_duration_hms': '01:35:00',
        'deep_percent': 23.17,
        'end_date_str': '2024-07-23 10:15:36+00:00',
        'rem_duration_hms': '01:46:00',
        'rem_percent': 25.85,
        'start_date_str': '2024-07-23 03:25:36+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
