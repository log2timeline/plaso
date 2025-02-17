#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Motherboard Info Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import motherboard_info

from tests.parsers.winreg_plugins import test_lib


class WindowsRegistryMotherboardInfoPluginTest(
    test_lib.RegistryPluginTestCase):
  """Tests for the Motherboard Info Windows Registry plugin."""

  def _CreateTestKey(self):
    """Creates Registry keys and values for testing.

    Returns:
      dfwinreg.WinRegistryKey: a Windows Registry key.
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromDateTimeString('2024-08-28 09:23:49.002031')
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
      'SystemInformation', key_path_prefix='HKEY_LOCAL_MACHINE\\System',
      last_written_time=filetime.timestamp,
      relative_key_path='ControlSet001\\Control\\SystemInformation')

    value_data = 'Microsoft Corporation'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
      'SystemManufacturer', data=value_data,
      data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = 'Virtual Machine'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
      'SystemProductName', data=value_data,
      data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = '05/13/2024'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
      'BIOSReleaseDate', data=value_data,
      data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = 'Hyper-V UEFI Release v4.1'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
      'BIOSVersion', data=value_data,
      data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcessValue(self):
    """Tests the Process function for BAM data."""
    test_file_entry = test_lib.TestFileEntry('SYSTEM')
    registry_key = self._CreateTestKey()
    plugin = motherboard_info.MotherboardInfoPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
      'data_type': 'windows:registry:motherboard_info',
      'motherboard_manufacturer': 'Microsoft Corporation',
      'motherboard_model': 'Virtual Machine',
      'bios_release_date': '05/13/2024',
      'bios_version': 'Hyper-V UEFI Release v4.1',
      'key_path': 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\'
                  'SystemInformation',
      'last_written_time': '2024-08-28T09:23:49.0020310+00:00'
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
