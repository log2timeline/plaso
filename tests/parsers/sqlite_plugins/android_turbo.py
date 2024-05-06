#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android turbo plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_turbo

from tests.parsers.sqlite_plugins import test_lib


class AndroidTurboSQLitePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android turbo database plugin."""

  def testProcess(self):
    """Tests the Process function on an Android turbo.db file."""
    plugin = android_turbo.AndroidTurboPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['android_turbo.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2717)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'battery_level': 99,
        'battery_saver': 2,
       'charge_type': 0,
       'recorded_time': '2023-05-27T13:06:46.000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'battery_level': 54,
        'battery_saver': 2,
        'charge_type': 1,
        'recorded_time': '2023-06-22T11:26:27.000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2138)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
