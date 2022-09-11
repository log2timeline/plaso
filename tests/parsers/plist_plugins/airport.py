#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Airport plist plugin."""

import unittest

from plaso.parsers.plist_plugins import airport

from tests.parsers.plist_plugins import test_lib


class MacOSAirportPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the MacOS Airport plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.airport.preferences.plist'

    plugin = airport.MacOSAirportPlistPlugin()
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

    expected_event_values = {
        'data_type': 'macos:airport:entry',
        'date_time': '2013-07-30 00:29:26',
        'security_type': 'WPA/WPA2 Personal',
        'ssid': 'europa'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
