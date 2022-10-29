#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Android logcat text parser plugin."""

import unittest

from plaso.parsers.text_plugins import android_logcat

from tests.parsers.text_plugins import test_lib


class AndroidLogcatTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Android logcat text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = android_logcat.AndroidLogcatTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['android_logcat.log'], plugin, knowledge_base_values={'year': 1990})

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check entry with recorded time with milliseconds precision in local time.
    expected_event_values = {
        'component_tag': 'threadtime',
        'data_type': 'android:logcat',
        'message': 'test of default threadtime format',
        'pid': 1234,
        'priority': 'D',
        'recorded_time': '1990-01-01T01:02:03.123',
        'thread_identifier': 1234}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check entry with recorded time with milliseconds precision with time
    # zone offset.
    expected_event_values = {
        'component_tag': 'App',
        'data_type': 'android:logcat',
        'message': 'test of threadtime w/ UTC and year',
        'pid': 1885,
        'priority': 'E',
        'recorded_time': '2022-01-02T01:20:03.171+00:00',
        'thread_identifier': 3066,
        'user_identifier': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Check entry with recorded time with microseconds precision in local time.
    expected_event_values = {
        'component_tag': 'App',
        'data_type': 'android:logcat',
        'message': 'test of threadtime w/ year, uid, usec',
        'pid': 1885,
        'priority': 'E',
        'recorded_time': '2022-01-02T01:20:07.171997',
        'thread_identifier': 3066,
        'user_identifier': 1000}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    # Check entry with recorded time with microseconds precision with time
    # zone offset.
    expected_event_values = {
        'component_tag': 'AppTag',
        'data_type': 'android:logcat',
        'message': 'test of threadtime w/ year, zone, usec',
        'pid': 9346,
        'priority': 'E',
        'recorded_time': '2022-01-02T11:20:07.171997+10:00',
        'thread_identifier': 9347,
        'user_identifier': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
