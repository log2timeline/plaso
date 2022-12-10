# -*- coding: utf-8 -*-
"""Tests for the SQLite parser plugin for iOS netusage database files."""

import unittest

from plaso.parsers.sqlite_plugins import ios_netusage

from tests.parsers.sqlite_plugins import test_lib


class IOSNetusagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite parser plugin for iOS netusage database files."""

  def testProcess(self):
    """Test the Process function."""
    plugin = ios_netusage.IOSNetusagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['netusage.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 384)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test a route database entry.
    expected_event_values = {
        'bytes_in': 131926734,
        'bytes_out': 59786697,
        'data_type': 'ios:netusage:route',
        'network_identifier': 'Carrier-18005506',
        'network_signature': '353537613832343930343563356433642D33613937333034',
        'network_type': 2,
        'start_time': '2021-02-19T05:00:00.000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test a process database entry.
    expected_event_values = {
        'data_type': 'ios:netusage:process',
        'process_name': 'mDNSResponder',
        'start_time': '2021-01-17T19:23:38.212656+00:00',
        'wifi_in': 79188353,
        'wifi_out': 35398277,
        'wired_in': 12198756,
        'wired_out': 10841,
        'wireless_wan_in': 300997,
        'wireless_wan_out': 938811}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 50)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
