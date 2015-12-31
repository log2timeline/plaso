#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the timezone Windows Registry plugin."""

import unittest

from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import timezone as winreg_timezone

from tests.parsers.winreg_plugins import test_lib


class WinRegTimezonePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the timezone Windows Registry plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = winreg_timezone.WinRegTimezonePlugin()

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path: the Windows Registry key path.
      time_string: string containing the key last written date and time.

    Returns:
      A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    filetime = dfwinreg_fake.Filetime()
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'TimeZoneInformation', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    value_data = u'C:\\Downloads\\plaso-static.rar'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'1', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=612)
    registry_key.AddValue(registry_value)

    value_data = b'\xff\xff\xff\xc4'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ActiveTimeBias', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = b'\xff\xff\xff\xc4'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Bias', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = b'\xff\xff\xff\xc4'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DaylightBias', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = u'@tzres.dll,-321'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DaylightName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = (
        b'\x00\x00\x03\x00\x05\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DaylightStart', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DynamicDaylightTimeDisabled', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'StandardBias', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = u'@tzres.dll,-322'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'StandardName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = (
        b'\x00\x00\x0A\x00\x05\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'StandardStart', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    registry_key.AddValue(registry_value)

    value_data = u'W. Europe Standard Time'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'TimeZoneKeyName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcessMock(self):
    """Tests the Process function on created key."""
    key_path = (
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\'
        u'TimeZoneInformation')
    time_string = u'2013-01-30 10:47:57'
    registry_key = self._CreateTestKey(key_path, time_string)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, registry_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'ActiveTimeBias: -60 '
        u'Bias: -60 '
        u'DaylightBias: -60 '
        u'DaylightName: @tzres.dll,-321 '
        u'DynamicDaylightTimeDisabled: 0 '
        u'StandardBias: 0 '
        u'StandardName: @tzres.dll,-322 '
        u'TimeZoneKeyName: W. Europe Standard Time').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_objects[0], expected_message, expected_short_message)

  def testProcessFile(self):
    """Tests the Process function on registry file."""
    test_file_entry = self._GetTestFileEntryFromPath([u'SYSTEM'])
    key_path = (
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\'
        u'TimeZoneInformation')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-11 07:00:00.000642')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'ActiveTimeBias: 240 '
        u'Bias: 300 '
        u'DaylightBias: -60 '
        u'DaylightName: @tzres.dll,-111 '
        u'DynamicDaylightTimeDisabled: 0 '
        u'StandardBias: 0 '
        u'StandardName: @tzres.dll,-112 '
        u'TimeZoneKeyName: Eastern Standard Time').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_objects[0], expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
