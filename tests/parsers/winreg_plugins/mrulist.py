#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MRUList Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import mrulist

from tests.parsers.winreg_plugins import test_lib


class TestMRUListStringPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the string MRUList plugin."""

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path: the Windows Registry key path.
      time_string: string containing the key last written date and time.

    Returns:
      A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'MRU', key_path=key_path, last_written_time=filetime.timestamp,
        offset=1456)

    value_data = u'acb'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'MRUList', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=123)
    registry_key.AddValue(registry_value)

    value_data = u'Some random text here'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'a', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    registry_key.AddValue(registry_value)

    value_data = u'c:/evil.exe'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'b', data=value_data, data_type=dfwinreg_definitions.REG_BINARY,
        offset=612)
    registry_key.AddValue(registry_value)

    value_data = u'C:/looks_legit.exe'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'c', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1001)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Some Windows\\'
        u'InterestingApp\\MRU')
    time_string = u'2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin_object = mrulist.MRUListStringPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin_object)

    self.assertEqual(storage_writer.number_of_events, 1)

    event_object = storage_writer.events[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, plugin_object.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value a]: Some random text here '
        u'Index: 2 [MRU Value c]: C:/looks_legit.exe '
        u'Index: 3 [MRU Value b]: c:/evil.exe').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


class TestMRUListShellItemListPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the shell item list MRUList plugin."""

  def _CreateTestKey(self, key_path, time_string):
    """Creates MRUList Registry keys and values for testing.

    Args:
      key_path: the Windows Registry key path.
      time_string: string containing the key last written date and time.

    Returns:
      A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'DesktopStreamMRU', key_path=key_path,
        last_written_time=filetime.timestamp, offset=1456)

    value_data = u'a'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'MRUList', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=123)
    registry_key.AddValue(registry_value)

    value_data = b''.join(map(chr, [
        0x14, 0x00, 0x1f, 0x00, 0xe0, 0x4f, 0xd0, 0x20, 0xea, 0x3a, 0x69, 0x10,
        0xa2, 0xd8, 0x08, 0x00, 0x2b, 0x30, 0x30, 0x9d, 0x19, 0x00, 0x23, 0x43,
        0x3a, 0x5c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x11, 0xee, 0x15, 0x00, 0x31,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x2e, 0x3e, 0x7a, 0x60, 0x10, 0x80, 0x57,
        0x69, 0x6e, 0x6e, 0x74, 0x00, 0x00, 0x18, 0x00, 0x31, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x2e, 0x3e, 0xe4, 0x62, 0x10, 0x00, 0x50, 0x72, 0x6f, 0x66,
        0x69, 0x6c, 0x65, 0x73, 0x00, 0x00, 0x25, 0x00, 0x31, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x2e, 0x3e, 0xe4, 0x62, 0x10, 0x00, 0x41, 0x64, 0x6d, 0x69,
        0x6e, 0x69, 0x73, 0x74, 0x72, 0x61, 0x74, 0x6f, 0x72, 0x00, 0x41, 0x44,
        0x4d, 0x49, 0x4e, 0x49, 0x7e, 0x31, 0x00, 0x17, 0x00, 0x31, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x2e, 0x3e, 0xe4, 0x62, 0x10, 0x00, 0x44, 0x65, 0x73,
        0x6b, 0x74, 0x6f, 0x70, 0x00, 0x00, 0x00, 0x00]))

    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'a', data=value_data, data_type=dfwinreg_definitions.REG_BINARY,
        offset=612)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\DesktopStreamMRU')
    time_string = u'2012-08-28 09:23:49.002031'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin_object = mrulist.MRUListShellItemListPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin_object)

    self.assertEqual(storage_writer.number_of_events, 5)

    # A MRUList event object.
    event_object = storage_writer.events[4]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, plugin_object.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value a]: Shell item path: '
        u'<My Computer> C:\\Winnt\\Profiles\\Administrator\\Desktop').format(
            key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    # A shell item event object.
    event_object = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-01-14 12:03:52')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'Name: Winnt '
        u'Shell item path: <My Computer> C:\\Winnt '
        u'Origin: {0:s}').format(key_path)
    expected_short_message = (
        u'Name: Winnt '
        u'Origin: HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\'
        u'CurrentVersi...')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
