#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the airport plist plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [
        1375144166000000, 1386874984000000, 1386949546000000, 1386950747000000]
    timestamps = sorted([event.timestamp for event in events])
    self.assertEqual(timestamps, expected_timestamps)

    event = events[0]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.key, 'item')
    self.assertEqual(event_data.root, '/RememberedNetworks')

    expected_description = (
        '[WiFi] Connected to network: <europa> using security '
        'WPA/WPA2 Personal')
    self.assertEqual(event_data.desc, expected_description)

    expected_message = '/RememberedNetworks/item {0:s}'.format(
        expected_description)
    expected_short_message = '{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
