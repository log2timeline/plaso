#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the timezone Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import timezone

from tests.parsers.winreg_plugins import test_lib


class WinRegTimezonePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the timezone Windows Registry plugin."""

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
        'TimeZoneInformation', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    value_data = 'C:\\Downloads\\plaso-static.rar'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        '1', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=612)
    registry_key.AddValue(registry_value)

    value_data = b'\xff\xff\xff\xc4'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ActiveTimeBias', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = b'\xff\xff\xff\xc4'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Bias', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = b'\xff\xff\xff\xc4'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DaylightBias', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = '@tzres.dll,-321'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DaylightName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = (
        b'\x00\x00\x03\x00\x05\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DaylightStart', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DynamicDaylightTimeDisabled', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'StandardBias', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = '@tzres.dll,-322'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'StandardName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = (
        b'\x00\x00\x0A\x00\x05\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'StandardStart', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY)
    registry_key.AddValue(registry_value)

    value_data = 'W. Europe Standard Time'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'TimeZoneKeyName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = timezone.WinRegTimezonePlugin()

    key_path = (
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\'
        'TimeZoneInformation')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcessMock(self):
    """Tests the Process function on created key."""
    key_path = (
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\'
        'TimeZoneInformation')
    time_string = '2013-01-30 10:47:57'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = timezone.WinRegTimezonePlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

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
        'configuration': (
            'ActiveTimeBias: -60 '
            'Bias: -60 '
            'DaylightBias: -60 '
            'DaylightName: @tzres.dll,-321 '
            'DynamicDaylightTimeDisabled: 0 '
            'StandardBias: 0 '
            'StandardName: @tzres.dll,-322 '
            'TimeZoneKeyName: W. Europe Standard Time'),
        'data_type': 'windows:registry:timezone',
        'key_path': key_path,
        'last_written_time': '2013-01-30T10:47:57.0000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessFile(self):
    """Tests the Process function on registry file."""
    test_file_entry = self._GetTestFileEntry(['SYSTEM'])
    key_path = (
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\'
        'TimeZoneInformation')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = timezone.WinRegTimezonePlugin()
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
        'configuration': (
            'ActiveTimeBias: 240 '
            'Bias: 300 '
            'DaylightBias: -60 '
            'DaylightName: @tzres.dll,-111 '
            'DynamicDaylightTimeDisabled: 0 '
            'StandardBias: 0 '
            'StandardName: @tzres.dll,-112 '
            'TimeZoneKeyName: Eastern Standard Time'),
        'data_type': 'windows:registry:timezone',
        'key_path': key_path,
        'last_written_time': '2012-03-11T07:00:00.0006424+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
