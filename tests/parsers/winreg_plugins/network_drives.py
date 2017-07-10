#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Network Drives Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
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
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'Network', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    # Setup H drive.
    h_key = dfwinreg_fake.FakeWinRegistryKey(
        u'H', last_written_time=filetime.timestamp)
    registry_key.AddSubkey(h_key)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ConnectionType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x04'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DeferFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProviderFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    value_data = u'Microsoft Windows Network'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProviderName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    h_key.AddValue(registry_value)

    value_data = b'\x00\x02\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProviderType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    value_data = u'\\\\acme.local\\Shares\\User_Data\\John.Doe'.encode(
        u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'RemotePath', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    h_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'UserName', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    h_key.AddValue(registry_value)

    # Setup Z drive.
    z_key = dfwinreg_fake.FakeWinRegistryKey(
        u'Z', last_written_time=filetime.timestamp)
    registry_key.AddSubkey(z_key)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ConnectionType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x04'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DeferFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProviderFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    value_data = u'Microsoft Windows Network'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProviderName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    z_key.AddValue(registry_value)

    value_data = b'\x00\x02\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProviderType', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    value_data = u'\\\\secret_computer\\Media'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'RemotePath', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    z_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'UserName', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    z_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function on created key."""
    key_path = u'HKEY_CURRENT_USER\\Network'
    time_string = u'2013-01-30 10:47:57'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = network_drives.NetworkDrivesPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetSortedEvents())

    event_object = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'DriveLetter: H '
        u'RemoteServer: acme.local '
        u'ShareName: \\Shares\\User_Data\\John.Doe '
        u'Type: Mapped Drive').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
