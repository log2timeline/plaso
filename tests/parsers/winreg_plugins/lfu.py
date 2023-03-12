#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Less Frequently Used (LFU) Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import lfu

from tests.parsers.winreg_plugins import test_lib


class BootExecutePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the LFU BootExecute Windows Registry plugin."""

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
        'Session Manager', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    value_data = 'autocheck autochk *\x00'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'BootExecute', data=value_data,
        data_type=dfwinreg_definitions.REG_MULTI_SZ, offset=123)
    registry_key.AddValue(registry_value)

    value_data = '2592000'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'CriticalSectionTimeout', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=153)
    registry_key.AddValue(registry_value)

    value_data = '\x00'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ExcludeFromKnownDlls', data=value_data,
        data_type=dfwinreg_definitions.REG_MULTI_SZ, offset=163)
    registry_key.AddValue(registry_value)

    value_data = '0'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'GlobalFlag', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=173)
    registry_key.AddValue(registry_value)

    value_data = '0'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'HeapDeCommitFreeBlockThreshold', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=183)
    registry_key.AddValue(registry_value)

    value_data = '0'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'HeapDeCommitTotalFreeThreshold', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=203)
    registry_key.AddValue(registry_value)

    value_data = '0'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'HeapSegmentCommit', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=213)
    registry_key.AddValue(registry_value)

    value_data = '0'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'HeapSegmentReserve', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=223)
    registry_key.AddValue(registry_value)

    value_data = '2'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'NumberOfInitialSessions', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=243)
    registry_key.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = lfu.BootExecutePlugin()

    key_path = (
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\Session Manager')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\Session Manager')
    time_string = '2012-08-31 20:45:29'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = lfu.BootExecutePlugin()
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
        'data_type': 'windows:registry:boot_execute',
        'key_path': key_path,
        'last_written_time': '2012-08-31T20:45:29.0000000+00:00',
        'value': 'autocheck autochk *'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'windows:registry:key_value',
        'key_path': key_path,
        'last_written_time': '2012-08-31T20:45:29.0000000+00:00',
        'values': [
            ('CriticalSectionTimeout', 'REG_SZ', '2592000'),
            ('ExcludeFromKnownDlls', 'REG_MULTI_SZ', '[]'),
            ('GlobalFlag', 'REG_SZ', '0'),
            ('HeapDeCommitFreeBlockThreshold', 'REG_SZ', '0'),
            ('HeapDeCommitTotalFreeThreshold', 'REG_SZ', '0'),
            ('HeapSegmentCommit', 'REG_SZ', '0'),
            ('HeapSegmentReserve', 'REG_SZ', '0'),
            ('NumberOfInitialSessions', 'REG_SZ', '2')]}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


class BootVerificationPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the LFU BootVerification Windows Registry plugin."""

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
        'BootVerificationProgram', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    value_data = 'C:\\WINDOWS\\system32\\googleupdater.exe'.encode(
        'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ImagePath', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=123)
    registry_key.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = lfu.BootVerificationPlugin()

    key_path = (
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\'
        'BootVerificationProgram')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    key_path = '\\ControlSet001\\Control\\BootVerificationProgram'
    time_string = '2012-08-31 20:45:29'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = lfu.BootVerificationPlugin()
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
        'data_type': 'windows:registry:boot_verification',
        'image_path': 'C:\\WINDOWS\\system32\\googleupdater.exe',
        'key_path': key_path,
        'last_written_time': '2012-08-31T20:45:29.0000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
