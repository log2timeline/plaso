#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the USB Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import usb

from tests.parsers.winreg_plugins import test_lib


class USBPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the USB Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = usb.USBPlugin()

    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USB'
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['SYSTEM'])
    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USB'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = usb.USBPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 7)

    events = list(storage_writer.GetEvents())

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2012-04-07 10:31:37.625247')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_data.parser, plugin.plugin_name)
    self.assertEqual(event_data.data_type, 'windows:registry:usb')
    self.assertEqual(event_data.pathspec, test_file_entry.path_spec)
    self.assertEqual(event_data.subkey_name, 'VID_0E0F&PID_0002')
    self.assertEqual(event_data.vendor, 'VID_0E0F')
    self.assertEqual(event_data.product, 'PID_0002')

    expected_message = (
        '[{0:s}] '
        'Product: PID_0002 '
        'Serial: 6&2ab01149&0&2 '
        'Subkey name: VID_0E0F&PID_0002 '
        'Vendor: VID_0E0F').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
