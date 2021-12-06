#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the airport plist plugin."""

import unittest

from plaso.parsers.plist_plugins import airport

from tests.parsers.plist_plugins import test_lib


class AirportPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the airport plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.airport.preferences.plist'

    plugin = airport.AirportPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [
        1375144166000000, 1386874984000000, 1386949546000000, 1386950747000000]
    timestamps = sorted([event.timestamp for event in events])
    self.assertEqual(timestamps, expected_timestamps)

    expected_event_values = {
        'data_type': 'plist:key',
        'desc': (
            '[WiFi] Connected to network: <europa> using security '
            'WPA/WPA2 Personal'),
        'key': 'item',
        'root': '/RememberedNetworks'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
