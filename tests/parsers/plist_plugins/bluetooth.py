#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Bluetooth plist plugin."""

import unittest

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

    expected_event_values = {
        'data_type': 'plist:key',
        'desc': 'Paired:True Name:Apple Magic Trackpad 2',
        'key': '44-00-00-00-00-04',
        'root': '/DeviceCache',
        'timestamp': '2012-11-02 01:13:17.324095'}

    self.CheckEventValues(storage_writer, events[10], expected_event_values)


if __name__ == '__main__':
  unittest.main()
