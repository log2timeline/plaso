#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for iOS Health Height SQLite database plugin (golden values)."""

import unittest

from plaso.parsers.sqlite_plugins import ios_health_height
from tests.parsers.sqlite_plugins import test_lib


class IOSHealthHeightPluginGoldenTest(test_lib.SQLitePluginTestCase):
  """Golden-value tests for the iOS Health Height SQLite database plugin."""

  def testProcess(self):
    """Tests the Process function on a healthdb_secure.sqlite file."""
    plugin = ios_health_height.IOSHealthHeightPlugin()
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
        'data_type': 'ios:health:height',
        'date_time': '2020-04-03T18:23:55+00:00',
        'height_cm': 177,
        'height_ft_in': "5'10\"",
        'height_m': 1.7780000000000002,
        'height_value_ts_str': '2020-04-03 18:23:55+00:00'}

    matched_index = None
    for i in range(number_of_event_data):
      event_data = storage_writer.GetAttributeContainerByIndex('event_data', i)
      if (getattr(event_data, 'height_cm', None) == 177 and
          getattr(event_data, 'height_ft_in', None) == "5'10\"" and
          getattr(event_data, 'height_value_ts_str', None) ==
          '2020-04-03 18:23:55+00:00'):
        matched_index = i
        break

    msg = 'Golden height event not found in parsed results.'
    self.assertIsNotNone(matched_index, msg=msg)

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', matched_index)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
  