#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the airport plist plugin."""

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import airport

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class AirportPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the airport plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([
      u'com.apple.airport.preferences.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.airport.preferences.plist'

    plugin = airport.AirportPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_events, 4)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [
        1375144166000000, 1386874984000000, 1386949546000000, 1386950747000000]
    timestamps = sorted([event.timestamp for event in events])
    self.assertEqual(timestamps, expected_timestamps)

    event = events[0]
    self.assertEqual(event.key, u'item')
    self.assertEqual(event.root, u'/RememberedNetworks')

    expecte_description = (
        u'[WiFi] Connected to network: <europa> using security '
        u'WPA/WPA2 Personal')
    self.assertEqual(event.desc, expecte_description)

    expected_message = u'/RememberedNetworks/item {0:s}'.format(
        expecte_description)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
