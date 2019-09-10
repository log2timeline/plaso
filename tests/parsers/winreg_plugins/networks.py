#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Networks Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import definitions
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
    profiles = dfwinreg_fake.FakeWinRegistryKey('Profiles')
    registry_key.AddSubkey(profiles)

    profile_1 = dfwinreg_fake.FakeWinRegistryKey(
        '{B358E985-4464-4ABD-AF99-7D4A0AF66BB7}')
    profiles.AddSubkey(profile_1)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Category', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_1.AddValue(registry_value)

    value_data = (
        b'\xde\x07\x0c\x00\x02\x00\x10\x00\x08\x00\x04\x00\x27\x00\x6a\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DateCreated', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile_1.AddValue(registry_value)

    value_data = (
        b'\xdf\x07\x01\x00\x02\x00\x1b\x00\x0f\x00\x0f\x00\x1b\x00\xc5\x03')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DateLastConnected', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile_1.AddValue(registry_value)

    value_data = 'My Awesome Wifi Hotspot'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Description', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile_1.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Managed', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_1.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x47'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'NameType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_1.AddValue(registry_value)

    value_data = 'My Awesome Wifi Hotspot'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProfileName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile_1.AddValue(registry_value)

    profile_2 = dfwinreg_fake.FakeWinRegistryKey(
        '{C1C57B58-BFE2-428B-818C-9D69A873AD3D}')
    profiles.AddSubkey(profile_2)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Category', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_2.AddValue(registry_value)

    value_data = (
        b'\xde\x07\x05\x00\x02\x00\x06\x00\x11\x00\x02\x00\x13\x00\x1b\x03')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DateCreated', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile_2.AddValue(registry_value)

    value_data = (
        b'\xde\x07\x05\x00\x02\x00\x06\x00\x11\x00\x07\x00\x36\x00\x0a\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DateLastConnected', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile_2.AddValue(registry_value)

    value_data = 'Network'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Description', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile_2.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Managed', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_2.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x06'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'NameType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_2.AddValue(registry_value)

    value_data = 'Network'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProfileName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile_2.AddValue(registry_value)

    # Setup signatures.
    signatures = dfwinreg_fake.FakeWinRegistryKey('Signatures')
    registry_key.AddSubkey(signatures)

    managed = dfwinreg_fake.FakeWinRegistryKey('Managed')
    signatures.AddSubkey(managed)

    unmanaged = dfwinreg_fake.FakeWinRegistryKey('Unmanaged')
    signatures.AddSubkey(unmanaged)

    unmanaged_subkey = dfwinreg_fake.FakeWinRegistryKey(
        '010103000F0000F0080000000F0000F0E8982FB31F37E52AF30A6575A4898CE667'
        '6E8C2F99C4C5131D84F64BD823E0')
    unmanaged.AddSubkey(unmanaged_subkey)

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
    time_string = '2013-01-30 10:47:57'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = networks.NetworksWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2014-05-06 17:02:19.795000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.data_type, 'windows:registry:network')

    expected_message = (
        'SSID: Network '
        'Description: Network '
        'Connection Type: Wired '
        'Default Gateway Mac: 00:50:56:ea:6c:ec '
        'DNS Suffix: localdomain')
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2015-01-27 15:15:27.965000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_CONNECTED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.data_type, 'windows:registry:network')

    expected_message = (
        'SSID: My Awesome Wifi Hotspot '
        'Description: My Awesome Wifi Hotspot '
        'Connection Type: Wireless')
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
