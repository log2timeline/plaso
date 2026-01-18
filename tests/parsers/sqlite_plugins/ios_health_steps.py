#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Steps SQLite database plugin (golden values)."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_steps
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthStepsPluginGoldenTest(test_lib.SQLitePluginTestCase):
  """Golden-value tests for the iOS Health Steps SQLite database plugin."""

  def testProcess(self):
    """Tests the Process function on a healthdb_secure.sqlite file."""
    plugin = ios_health_steps.IOSHealthStepsPlugin()
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
        'data_type': 'ios:health:steps',
        'date_time': '2023-10-27T10:00:00+00:00',
        'device': 'iPhone15,2',
        'duration': 60.0,
        'end_date_str': '2023-10-27T10:01:00+00:00',
        'start_date_str': '2023-10-27T10:00:00+00:00',
        'steps': 120}

    matched_index = None
    for i in range(number_of_event_data):
      event_data = storage_writer.GetAttributeContainerByIndex('event_data', i)
      if (getattr(event_data, 'steps', None) == 120 and
          getattr(event_data, 'device', None) == 'iPhone15,2' and
          getattr(event_data, 'start_date_str', None) ==
          '2023-10-27T10:00:00+00:00'):
        matched_index = i
        break

    msg = 'Golden steps event not found in parsed results.'
    self.assertIsNotNone(matched_index, msg=msg)

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', matched_index)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
