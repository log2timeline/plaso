#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the USB Windows Registry plugin."""

import unittest

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

    expected_event_values = {
        'data_type': 'windows:registry:usb',
        'key_path': key_path,
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.plugin_name,
        'product': 'PID_0002',
        'serial': '6&2ab01149&0&2',
        'subkey_name': 'VID_0E0F&PID_0002',
        'timestamp': '2012-04-07 10:31:37.625247',
        'vendor': 'VID_0E0F'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)


if __name__ == '__main__':
  unittest.main()
