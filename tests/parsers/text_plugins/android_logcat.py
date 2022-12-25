#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Android logcat text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import android_logcat

from tests.parsers.text_plugins import test_lib


class AndroidLogcatTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Android logcat text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = android_logcat.AndroidLogcatTextPlugin()

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'--------- beginning of main\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

  def testProcess(self):
    """Tests the Process function."""
    plugin = android_logcat.AndroidLogcatTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['android_logcat.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check entry with recorded time without a year with milliseconds precision
    # in local time.
    expected_event_values = {
        'component_tag': 'threadtime',
        'data_type': 'android:logcat',
        'message': 'test of default threadtime format',
        'pid': 1234,
        'priority': 'D',
        'recorded_time': '0000-01-01T01:02:03.123',
        'thread_identifier': 1234}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check entry with recorded time with a year and milliseconds precision
    # with a time zone offset.
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

    # Check entry with recorded time with a year and microseconds precision
    # in local time.
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

    # Check entry with recorded time with a year and microseconds precision
    # with time a zone offset.
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
