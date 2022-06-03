# -*- coding: utf-8 -*-
"""Tests for the SQLite parser plugin for iOS Screen Time database files."""

import unittest

from plaso.parsers.sqlite_plugins import ios_screentime

from tests.parsers.sqlite_plugins import test_lib


class IOSScreenTimePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite parser plugin for iOS Screen Time database files."""

  def testParse(self):
    """Tests the ParseScreenTimeRow method."""
    plugin = ios_screentime.IOSScreenTimePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['ios_screentime.sqlite'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 777)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'bundle_identifier': 'com.spotify.client',
        'device_identifier': 'c623fbd7e91b041e07a68f8523f53a35973e475d',
        'device_name': 'iPhone',
        'domain': None,
        'total_time': 1006,
        'user_family_name': 'DFIR',
        'user_given_name': 'This Is',
        'timestamp': '2021-02-03 16:00:00.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'bundle_identifier': None,
        'device_identifier': None,
        'device_name': None,
        'domain': 'blog.d204n6.com',
        'total_time': 38,
        'user_family_name': 'DFIR',
        'user_given_name': 'This Is',
        'timestamp': '2021-02-17 21:00:00.000000'}

    self.CheckEventValues(storage_writer, events[145], expected_event_values)


if __name__ == '__main__':
  unittest.main()
