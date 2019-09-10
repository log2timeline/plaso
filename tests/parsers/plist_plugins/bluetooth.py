#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Bluetooth plist plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import bluetooth

from tests.parsers.plist_plugins import test_lib


class TestBluetoothPlugin(test_lib.PlistPluginTestCase):
  """Tests for the Bluetooth plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    test_file_name = 'plist_binary'
    plist_name = 'com.apple.bluetooth.plist'

    plugin = bluetooth.BluetoothPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [test_file_name], plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 14)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    paired_events = []
    timestamps = []
    for event in events:
      timestamps.append(event.timestamp)

      event_data = self._GetEventDataOfEvent(storage_writer, event)
      if event_data.desc.startswith('Paired'):
        paired_events.append(event)

    # Ensure all 14 events and times from the plist are parsed correctly.
    self.assertEqual(len(timestamps), 14)

    expected_timestamps = frozenset([
        1341957896010535, 1341957896010535, 1350666385239662, 1350666391557044,
        1341957900020117, 1302199013524275, 1301012201414766, 1351818797324095,
        1351818797324095, 1351819298997673, 1351818803000000, 1351827808261762,
        1345251268370453, 1345251192528750])

    self.assertEqual(frozenset(timestamps), expected_timestamps)

    # Ensure two paired devices are matched.
    self.assertEqual(len(paired_events), 2)

    # One of the paired event descriptions should contain the string:
    # Paired:True Name:Apple Magic Trackpad 2.
    paired_descriptions = []
    for event in paired_events:
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      paired_descriptions.append(event_data.desc)

    self.assertTrue(
        'Paired:True Name:Apple Magic Trackpad 2' in paired_descriptions)

    event = events[10]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_string = (
        '/DeviceCache/44-00-00-00-00-04 '
        'Paired:True '
        'Name:Apple Magic Trackpad 2')

    self._TestGetMessageStrings(
        event_data, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
