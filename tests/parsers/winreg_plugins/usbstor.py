#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the USBStor Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import usbstor

from tests.parsers.winreg_plugins import test_lib


class USBStorPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the USBStor Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = usbstor.USBStorPlugin()

    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USBSTOR'
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['SYSTEM'])
    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USBSTOR'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = usbstor.USBStorPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:registry:usbstor:instance',
        'device_last_arrival_time': None,
        'device_last_removal_time': None,
        'device_type': 'Disk',
        'display_name': 'HP v100w USB Device',
        'driver_first_installation_time': '2011-04-01T04:52:38.6860000+00:00',
        'driver_last_installation_time': '2011-04-01T04:52:38.6860000+00:00',
        'firmware_time': None,
        'key_path': (
            '{0:s}\\Disk&Ven_HP&Prod_v100w&Rev_1024\\AA951D0000007252&0'.format(
                key_path)),
        'product': 'Prod_v100w',
        'revision': 'Rev_1024',
        'vendor': 'Ven_HP'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
