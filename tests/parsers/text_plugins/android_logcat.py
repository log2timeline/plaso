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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'component_tag': 'threadtime',
        'data_type': 'android:logcat',
        'date_time': '1990-01-01 01:02:03.123000',
        'message': 'test of default threadtime format',
        'pid': '1234',
        'priority': 'D',
        'thread_identifier': '1234'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'component_tag': 'sometag',
        'data_type': 'android:logcat',
        'date_time': '1990-01-02 01:02:04.156000',
        'message': 'test of default time format',
        'pid': '190',
        'priority': 'I',
        'thread_identifier': None}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'component_tag': 'App',
        'data_type': 'android:logcat',
        'date_time': '2022-01-02 01:20:03.171000',
        'message': 'test of threadtime w/ UTC and year',
        'pid': '1885',
        'priority': 'E',
        'thread_identifier': '3066' ,
        'user_identifier': None}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'component_tag': 'App',
        'data_type': 'android:logcat',
        'date_time': '2022-01-02 01:20:03.171000',
        'message': 'test of threadtime w/ UTC, year and uid',
        'pid': '1885',
        'priority': 'E',
        'thread_identifier': '3066' ,
        'user_identifier': '1000'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'component_tag': 'App',
        'data_type': 'android:logcat',
        'date_time': '2022-01-02 01:20:07.171997',
        'message': 'test of threadtime w/ year, uid, usec',
        'pid': '1885',
        'priority': 'E',
        'thread_identifier': '3066' ,
        'user_identifier': '1000'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'component_tag': 'AppTag',
        'data_type': 'android:logcat',
        'date_time': '2022-01-02 11:20:07.171997',
        'message': 'test of threadtime w/ year, zone, usec',
        'pid': '9346',
        'priority': 'E',
        'thread_identifier': '9347' ,
        'user_identifier': None}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'component_tag': 'AppTag',
        'data_type': 'android:logcat',
        'date_time': '2022-01-02 11:42:10.613472',
        'message': 'test of time w/ zone, uid, year',
        'pid': '1179',
        'priority': 'I',
        'thread_identifier': None,
        'user_identifier': '1080'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'component_tag': 'AppTag',
        'data_type': 'android:logcat',
        'date_time': '2022-01-02 11:44:23.183801',
        'message': 'test of time w/ zone, year',
        'pid': '1179',
        'priority': 'I',
        'thread_identifier': None,
        'user_identifier': None}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)


if __name__ == '__main__':
  unittest.main()
