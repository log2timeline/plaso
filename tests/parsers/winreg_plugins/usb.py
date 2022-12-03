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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 7)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:registry:usb',
        'key_path': key_path,
        'last_written_time': '2012-04-07T10:31:37.6252465+00:00',
        'product': 'PID_0002',
        'serial': '6&2ab01149&0&2',
        'subkey_name': 'VID_0E0F&PID_0002',
        'vendor': 'VID_0E0F'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
