#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Weight SQLite database plugin (golden values)."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_weight
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthWeightPluginGoldenTest(test_lib.SQLitePluginTestCase):
  """Golden-value tests for the iOS Health Weight SQLite database plugin."""

  def testProcess(self):
    """Tests the Process function on a healthdb_secure.sqlite file."""
    plugin = ios_health_weight.IOSHealthWeightPlugin()
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
        'data_type': 'ios:health:weight',
        'date_time': '2023-10-27T10:00:00+00:00',
        'weight_kg_str': '81.64',
        'weight_lbs_str': '180.00',
        'weight_stone_str': '12 Stone 12 Pounds',
        'weight_value_ts_str': '2023-10-27 10:00:00+00:00'}

    matched_index = None
    for i in range(number_of_event_data):
      event_data = storage_writer.GetAttributeContainerByIndex('event_data', i)
      if (getattr(event_data, 'weight_kg_str', None) == '81.64' and
          getattr(event_data, 'weight_value_ts_str', None) ==
          '2023-10-27 10:00:00+00:00'):
        matched_index = i
        break

    msg = 'Golden weight event not found in parsed results.'
    self.assertIsNotNone(matched_index, msg=msg)

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', matched_index)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
