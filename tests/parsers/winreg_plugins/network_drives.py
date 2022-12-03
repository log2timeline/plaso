#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Network Drives Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import network_drives

from tests.parsers.winreg_plugins import test_lib


class NetworkDrivesPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Network Drives Windows Registry plugin."""

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path (str): Windows Registry key path.
      time_string (str): key last written date and time.

    Returns:
      dfwinreg.WinRegistryKey: Windows Registry key.
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromDateTimeString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Network', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    # Setup H drive.
    h_key_name = 'H'
    h_key = dfwinreg_fake.FakeWinRegistryKey(
        h_key_name, last_written_time=filetime.timestamp)
    registry_key.AddSubkey(h_key_name, h_key)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ConnectionType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x04'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DeferFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProviderFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    value_data = 'Microsoft Windows Network'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProviderName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    h_key.AddValue(registry_value)

    value_data = b'\x00\x02\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProviderType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    value_data = '\\\\acme.local\\Shares\\User_Data\\John.Doe'.encode(
        'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'RemotePath', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    h_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'UserName', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    # Setup Z drive.
    z_key_name = 'Z'
    z_key = dfwinreg_fake.FakeWinRegistryKey(
        z_key_name, last_written_time=filetime.timestamp)
    registry_key.AddSubkey(z_key_name, z_key)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ConnectionType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x04'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DeferFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProviderFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    value_data = 'Microsoft Windows Network'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProviderName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    z_key.AddValue(registry_value)

    value_data = b'\x00\x02\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProviderType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    value_data = '\\\\secret_computer\\Media'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'RemotePath', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    z_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'UserName', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = network_drives.NetworkDrivesPlugin()

    self._AssertFiltersOnKeyPath(plugin, 'HKEY_CURRENT_USER\\Network')

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function on created key."""
    key_path = 'HKEY_CURRENT_USER\\Network'
    registry_key = self._CreateTestKey(key_path, '2013-01-30 10:47:57')

    plugin = network_drives.NetworkDrivesPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

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
        'data_type': 'windows:registry:network_drive',
        'drive_letter': 'H',
        'key_path': key_path,
        'last_written_time': '2013-01-30T10:47:57.0000000+00:00',
        'server_name': 'acme.local',
        'share_name': '\\Shares\\User_Data\\John.Doe'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
