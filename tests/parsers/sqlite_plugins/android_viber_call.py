#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android Viber call history plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_viber_call

from tests.parsers.sqlite_plugins import test_lib


class AndroidViberCallSQLitePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android Viber Call History database plugin."""

  def testProcess(self):
    """Test the Process function on an Android viber_data file."""
    plugin = android_viber_call.AndroidViberCallPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['viber_data'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'type': 2,
        'data_type': 'android:viber:call',
        'duration': 105,
        'number': '+19198887386',
        'start_time': '2022-11-25T20:43:08.267+00:00',
        'end_time': '2022-11-25T20:44:53.267+00:00',
        'viber_call_type': 4}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
