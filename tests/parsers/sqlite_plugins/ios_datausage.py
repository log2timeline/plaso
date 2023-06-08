# -*- coding: utf-8 -*-
"""Tests for the SQLite parser plugin for iOS datausage database files."""

import unittest

from plaso.parsers.sqlite_plugins import ios_datausage

from tests.parsers.sqlite_plugins import test_lib


class IOSDataUsagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite parser plugin for iOS data database files."""

  def testProcess(self):
    """Test the Process function."""
    plugin = ios_datausage.IOSDatausagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['DataUsage.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 887)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'bundle_identifier': None,
        'process_name': 'CumulativeUsageTracker',
        'start_time': '2023-04-11T14:45:15.450549+00:00',
        'wifi_in': 0,
        'wifi_out': 0,
        'wireless_wan_in': 1185814689,
        'wireless_wan_out': 150}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'bundle_identifier': 'com.apple.MobileSMS',
        'process_name': 'mDNSResponder/com.apple.MobileSMS',
        'start_time': '2023-05-15T20:58:15.839447+00:00',
        'wifi_in': 0,
        'wifi_out': 0,
        'wireless_wan_in': 4498,
        'wireless_wan_out': 1408}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 332)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
