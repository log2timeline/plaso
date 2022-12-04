#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Networks Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import networks

from tests.parsers.winreg_plugins import test_lib


class NetworksWindowsRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Networks Windows Registry plugin."""

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path (str): Windows Registry key path.
      time_string (str): key last written date and time.

    Returns:
      dfwinreg.WinRegistryKey: a Windows Registry key.
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromDateTimeString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'NetworkList', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    # Setup Profiles.
    profiles_key_name = 'Profiles'
    profiles_key = dfwinreg_fake.FakeWinRegistryKey(profiles_key_name)
    registry_key.AddSubkey(profiles_key_name, profiles_key)

    profile1_key_name = '{B358E985-4464-4ABD-AF99-7D4A0AF66BB7}'
    profile1_key = dfwinreg_fake.FakeWinRegistryKey(profile1_key_name)
    profiles_key.AddSubkey(profile1_key_name, profile1_key)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Category', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile1_key.AddValue(registry_value)

    value_data = (
        b'\xde\x07\x0c\x00\x02\x00\x10\x00\x08\x00\x04\x00\x27\x00\x6a\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DateCreated', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile1_key.AddValue(registry_value)

    value_data = (
        b'\xdf\x07\x01\x00\x02\x00\x1b\x00\x0f\x00\x0f\x00\x1b\x00\xc5\x03')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DateLastConnected', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile1_key.AddValue(registry_value)

    value_data = 'My Awesome Wifi Hotspot'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Description', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile1_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Managed', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile1_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x47'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'NameType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile1_key.AddValue(registry_value)

    value_data = 'My Awesome Wifi Hotspot'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProfileName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile1_key.AddValue(registry_value)

    profile2_key_name = '{C1C57B58-BFE2-428B-818C-9D69A873AD3D}'
    profile2_key = dfwinreg_fake.FakeWinRegistryKey(profile2_key_name)
    profiles_key.AddSubkey(profile2_key_name, profile2_key)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Category', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile2_key.AddValue(registry_value)

    value_data = (
        b'\xde\x07\x05\x00\x02\x00\x06\x00\x11\x00\x02\x00\x13\x00\x1b\x03')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DateCreated', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile2_key.AddValue(registry_value)

    value_data = (
        b'\xde\x07\x05\x00\x02\x00\x06\x00\x11\x00\x07\x00\x36\x00\x0a\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DateLastConnected', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile2_key.AddValue(registry_value)

    value_data = 'Network'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Description', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile2_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Managed', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile2_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x06'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'NameType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile2_key.AddValue(registry_value)

    value_data = 'Network'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProfileName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile2_key.AddValue(registry_value)

    # Setup signatures.
    signatures_key_name = 'Signatures'
    signatures_key = dfwinreg_fake.FakeWinRegistryKey(signatures_key_name)
    registry_key.AddSubkey(signatures_key_name, signatures_key)

    managed_key_name = 'Managed'
    managed_key = dfwinreg_fake.FakeWinRegistryKey(managed_key_name)
    signatures_key.AddSubkey(managed_key_name, managed_key)

    unmanaged_key_name = 'Unmanaged'
    unmanaged_key = dfwinreg_fake.FakeWinRegistryKey(unmanaged_key_name)
    signatures_key.AddSubkey(unmanaged_key_name, unmanaged_key)

    unmanaged_subkey_name = (
        '010103000F0000F0080000000F0000F0E8982FB31F37E52AF30A6575A4898CE667'
        '6E8C2F99C4C5131D84F64BD823E0')
    unmanaged_subkey = dfwinreg_fake.FakeWinRegistryKey(unmanaged_subkey_name)
    unmanaged_key.AddSubkey(unmanaged_subkey_name, unmanaged_subkey)

    value_data = b'\x00\x50\x56\xea\x6c\xec'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DefaultGatewayMac', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    unmanaged_subkey.AddValue(registry_value)

    value_data = 'Network'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Description', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    unmanaged_subkey.AddValue(registry_value)

    value_data = 'localdomain'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DnsSuffix', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    unmanaged_subkey.AddValue(registry_value)

    value_data = 'Network'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'FirstNetwork', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    unmanaged_subkey.AddValue(registry_value)

    value_data = '{C1C57B58-BFE2-428B-818C-9D69A873AD3D}'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProfileGuid', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    unmanaged_subkey.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x08'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Source', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    unmanaged_subkey.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = networks.NetworksWindowsRegistryPlugin()

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion\\'
        'NetworkList')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function on created key."""
    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
    registry_key = self._CreateTestKey(key_path, '2013-01-30 10:47:57')

    plugin = networks.NetworksWindowsRegistryPlugin()
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
        'connection_type': 6,
        'creation_time': '2014-05-06T17:02:19.795+00:00',
        'data_type': 'windows:registry:network',
        'default_gateway_mac': '00:50:56:ea:6c:ec',
        'description': 'Network',
        'dns_suffix': 'localdomain',
        'last_connected_time': '2014-05-06T17:07:54.010+00:00',
        'ssid': 'Network'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
