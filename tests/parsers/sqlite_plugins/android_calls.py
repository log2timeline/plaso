#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android SMS call history plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_calls

from tests.parsers.sqlite_plugins import test_lib


class AndroidCallSQLitePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android Call History database plugin."""

  def testProcess(self):
    """Test the Process function on an Android contacts2.db file."""
    plugin = android_calls.AndroidCallPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['contacts2.db'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'call_type': 'MISSED',
        'data_type': 'android:event:call',
        'date_time': '2013-11-06 21:17:16.690',
        'number': '5404561685',
        'timestamp_desc': 'Call Started'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'android:event:call',
        'date_time': '2013-11-07 00:03:36.690'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'data_type': 'android:event:call',
        'date_time': '2013-11-07 00:14:15.690',
        'duration': 639,
        'timestamp_desc': 'Call Ended'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)


if __name__ == '__main__':
  unittest.main()
