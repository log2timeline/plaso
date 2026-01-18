#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Watch Worn Data SQLite plugin (golden values)."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_watch_worn_data
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWatchWornGoldenTest(test_lib.SQLitePluginTestCase):
  """Golden-value tests for the iOS Health Watch Worn Data SQLite plugin."""

  def testProcess(self):
    """Tests the Process function on a healthdb_secure.sqlite file."""
    plugin = ios_health_watch_worn_data.IOSHealthWatchWornPlugin()
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
        'data_type': 'ios:health:watch_worn',
        'date_time': '2020-03-22T00:00:00+00:00',
        'hours_off_before_next': 8,
        'hours_worn': 3,
        'last_worn_time_str': '2020-03-22 03:00:00+00:00',
        'start_time_str': '2020-03-22 00:00:00+00:00'}

    matched_index = None
    for i in range(number_of_event_data):
      event_data = storage_writer.GetAttributeContainerByIndex('event_data', i)
      if (getattr(event_data, 'start_time_str', None) ==
          expected_event_values['start_time_str'] and
          getattr(event_data, 'last_worn_time_str', None) ==
          expected_event_values['last_worn_time_str'] and
          getattr(event_data, 'hours_worn', None) ==
          expected_event_values['hours_worn'] and
          getattr(event_data, 'hours_off_before_next', None) ==
          expected_event_values['hours_off_before_next']):
        matched_index = i
        break

    msg = 'Golden watch-worn event not found in parsed results.'
    self.assertIsNotNone(matched_index, msg=msg)

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', matched_index)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
