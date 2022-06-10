# -*- coding: utf-8 -*-
"""Tests for the SQLite parser plugin for iOS netusage database files."""

import unittest

from plaso.parsers.sqlite_plugins import ios_netusage

from tests.parsers.sqlite_plugins import test_lib


class IOSNetusagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the SQLite parser plugin for iOS netusage database files."""

  def testParseNetusageRouteRow(self):
    """Tests the ParseNetusageRouteRow method."""
    plugin = ios_netusage.IOSNetusagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['netusage.sqlite'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 384)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'bytes_in': 131926734,
        'bytes_out': 59786697,
        'network_identifier': 'Carrier-18005506',
        'network_signature': '353537613832343930343563356433642D33613937333034',
        'network_type': 2,
        'timestamp': '2021-02-19 05:00:00.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'bytes_in': 34148,
        'bytes_out': 42416,
        'network_identifier': 'CcookiesDcastleR5 Guest-f8:bb:bf:8d:b9:c9',
        'network_signature': 'D9BA0E7A16AECFFC9DD5E8DC19242A49F7B2567900000000',
        'network_type': 1,
        'timestamp': '2021-02-19 05:00:00.000000'}

    self.CheckEventValues(storage_writer, events[17], expected_event_values)

  def testParseNetusageProcessRow(self):
    """Tests the ParseNetusageProcessRow method."""
    plugin = ios_netusage.IOSNetusagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['netusage.sqlite'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 384)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'process_name': 'mDNSResponder',
        'wifi_in': 79188353,
        'wifi_out': 35398277,
        'wired_in': 12198756,
        'wired_out': 10841,
        'wireless_wan_in': 300997,
        'wireless_wan_out': 938811,
        'timestamp': '2021-01-17 19:23:38.212656'}

    self.CheckEventValues(storage_writer, events[50], expected_event_values)

    expected_event_values = {
        'process_name': 'imgurmobile',
        'wifi_in': 31296315,
        'wifi_out': 435462,
        'wired_in': 0,
        'wired_out': 0,
        'wireless_wan_in': 0,
        'wireless_wan_out': 0,
        'timestamp': '2021-02-19 01:06:15.397861'}

    self.CheckEventValues(storage_writer, events[376], expected_event_values)


if __name__ == '__main__':
  unittest.main()
