#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Less Frequently Used (LFU) Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import lfu

from tests.parsers.winreg_plugins import test_lib


class TestBootExecutePlugin(test_lib.RegistryPluginTestCase):
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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    self.CheckTimestamp(event.timestamp, '2012-08-31 20:45:29.000000')

    expected_message = (
        '[{0:s}] BootExecute: autocheck autochk *').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    expected_message = (
        '[{0:s}] '
        'CriticalSectionTimeout: 2592000 '
        'ExcludeFromKnownDlls: [] '
        'GlobalFlag: 0 '
        'HeapDeCommitFreeBlockThreshold: 0 '
        'HeapDeCommitTotalFreeThreshold: 0 '
        'HeapSegmentCommit: 0 '
        'HeapSegmentReserve: 0 '
        'NumberOfInitialSessions: 2').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


class TestBootVerificationRegistry(test_lib.RegistryPluginTestCase):
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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    self.CheckTimestamp(event.timestamp, '2012-08-31 20:45:29.000000')

    expected_message = (
        '[{0:s}] '
        'ImagePath: C:\\WINDOWS\\system32\\googleupdater.exe').format(
            key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
