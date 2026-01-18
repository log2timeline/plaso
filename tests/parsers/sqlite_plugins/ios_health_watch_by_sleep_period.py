#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS Health - Watch by Sleep Period InBed plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_watch_by_sleep_period
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWatchBySleepPeriodPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the iOS Health - Watch by Sleep Period InBed plugin."""

  def testProcess(self):
    """Test overall plugin handling including parsing a real SQLite file."""
    plugin = (
        ios_health_watch_by_sleep_period.IOSHealthWatchBySleepPeriodPlugin())

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
        'asleep_percent': 25.61,
        'data_type': 'ios:health:watch_by_sleep_period',
        'end_date_str': '2024-07-23 10:15:36+00:00',
        'in_bed_duration_hms': '05:05:00',
        'in_bed_percent': 74.39,
        'start_date_str': '2024-07-23 03:25:36+00:00',
        'time_in_bed_hms': '06:50:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
