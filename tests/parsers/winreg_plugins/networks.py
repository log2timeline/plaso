#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Networks Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import networks

from tests.parsers.winreg_plugins import test_lib


class NetworksPluginTest(test_lib.RegistryPluginTestCase):
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
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'NetworkList', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    # Setup Profiles.
    profiles = dfwinreg_fake.FakeWinRegistryKey(u'Profiles')
    registry_key.AddSubkey(profiles)

    profile_1 = dfwinreg_fake.FakeWinRegistryKey(
        u'{B358E985-4464-4ABD-AF99-7D4A0AF66BB7}')
    profiles.AddSubkey(profile_1)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Category', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_1.AddValue(registry_value)

    value_data = (
        b'\xde\x07\x0c\x00\x02\x00\x10\x00\x08\x00\x04\x00\x27\x00\x6a\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DateCreated', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile_1.AddValue(registry_value)

    value_data = (
        b'\xdf\x07\x01\x00\x02\x00\x1b\x00\x0f\x00\x0f\x00\x1b\x00\xc5\x03')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DateLastConnected', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile_1.AddValue(registry_value)

    value_data = u'My Awesome Wifi Hotspot'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Description', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile_1.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Managed', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_1.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x47'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'NameType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_1.AddValue(registry_value)

    value_data = u'My Awesome Wifi Hotspot'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProfileName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile_1.AddValue(registry_value)

    profile_2 = dfwinreg_fake.FakeWinRegistryKey(
        u'{C1C57B58-BFE2-428B-818C-9D69A873AD3D}')
    profiles.AddSubkey(profile_2)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Category', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_2.AddValue(registry_value)

    value_data = (
        b'\xde\x07\x05\x00\x02\x00\x06\x00\x11\x00\x02\x00\x13\x00\x1b\x03')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DateCreated', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile_2.AddValue(registry_value)

    value_data = (
        b'\xde\x07\x05\x00\x02\x00\x06\x00\x11\x00\x07\x00\x36\x00\x0a\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DateLastConnected', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    profile_2.AddValue(registry_value)

    value_data = u'Network'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Description', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile_2.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Managed', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_2.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x06'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'NameType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    profile_2.AddValue(registry_value)

    value_data = u'Network'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProfileName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    profile_2.AddValue(registry_value)

    # Setup signatures.
    signatures = dfwinreg_fake.FakeWinRegistryKey(u'Signatures')
    registry_key.AddSubkey(signatures)

    managed = dfwinreg_fake.FakeWinRegistryKey(u'Managed')
    signatures.AddSubkey(managed)

    unmanaged = dfwinreg_fake.FakeWinRegistryKey(u'Unmanaged')
    signatures.AddSubkey(unmanaged)

    unmanaged_subkey = dfwinreg_fake.FakeWinRegistryKey(
        u'010103000F0000F0080000000F0000F0E8982FB31F37E52AF30A6575A4898CE667'
        u'6E8C2F99C4C5131D84F64BD823E0')
    unmanaged.AddSubkey(unmanaged_subkey)

    value_data = b'\x00\x50\x56\xea\x6c\xec'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DefaultGatewayMac', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    unmanaged_subkey.AddValue(registry_value)

    value_data = u'Network'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Description', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    unmanaged_subkey.AddValue(registry_value)

    value_data = u'localdomain'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DnsSuffix', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    unmanaged_subkey.AddValue(registry_value)

    value_data = u'Network'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'FirstNetwork', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    unmanaged_subkey.AddValue(registry_value)

    value_data = u'{C1C57B58-BFE2-428B-818C-9D69A873AD3D}'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProfileGuid', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    unmanaged_subkey.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x08'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Source', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    unmanaged_subkey.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function on created key."""
    key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
    time_string = u'2013-01-30 10:47:57'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = networks.NetworksPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-05-06 17:02:19.795')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_message = (
        u'SSID: Network '
        u'Description: Network '
        u'Connection Type: Wired '
        u'Default Gateway Mac: 00:50:56:ea:6c:ec '
        u'DNS Suffix: localdomain')
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-01-27 15:15:27.965')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_CONNECTED)

    expected_message = (
        u'SSID: My Awesome Wifi Hotspot '
        u'Description: My Awesome Wifi Hotspot '
        u'Connection Type: Wireless')
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
