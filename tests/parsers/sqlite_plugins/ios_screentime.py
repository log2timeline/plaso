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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 777)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'bundle_identifier': 'com.spotify.client',
        'device_identifier': 'c623fbd7e91b041e07a68f8523f53a35973e475d',
        'device_name': 'iPhone',
        'domain': None,
        'start_time': '2021-02-03T16:00:00.000000+00:00',
        'total_time': 1006,
        'user_family_name': 'DFIR',
        'user_given_name': 'This Is'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
