#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Bluetooth plist plugin."""

import unittest

from plaso.parsers.plist_plugins import bluetooth

from tests.parsers.plist_plugins import test_lib


class MacOSBluetoothPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the MacOS Bluetooth plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = bluetooth.MacOSBluetoothPlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, ['plist_binary'], 'com.apple.bluetooth.plist')

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'macos:bluetooth:entry',
        'device_identifier': '44-00-00-00-00-04',
        'device_name': 'Apple Magic Trackpad 2',
        'inquiry_time': '2012-11-02T01:13:17.324095+00:00',
        'is_paired': True,
        'name_update_time': '2012-11-02T01:21:38.997673+00:00',
        'services_update_time': '2012-11-02T01:13:23.000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
