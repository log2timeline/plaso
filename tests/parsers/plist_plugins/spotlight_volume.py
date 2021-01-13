#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Spotlight Volume configuration plist plugin."""

import unittest

from plaso.parsers.plist_plugins import spotlight_volume

from tests.parsers.plist_plugins import test_lib


class SpotlightVolumePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Spotlight Volume configuration plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'VolumeConfiguration.plist'

    plugin = spotlight_volume.SpotlightVolumePlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = [1369657656000000, 1372139683000000]
    timestamps = sorted([event.timestamp for event in events])

    self.assertEqual(timestamps, expected_timestamps)

    expected_event_values = {
        'data_type': 'plist:key',
        'desc': (
            'Spotlight Volume 4D4BFEB5-7FE6-4033-AAAA-AAAABBBBCCCCDDDD '
            '(/.MobileBackups) activated.'),
        'key': '',
        'root': '/Stores'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
