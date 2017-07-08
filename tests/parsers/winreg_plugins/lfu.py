#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Less Frequently Used (LFU) Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
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
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'Session Manager', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    value_data = u'autocheck autochk *\x00'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'BootExecute', data=value_data,
        data_type=dfwinreg_definitions.REG_MULTI_SZ, offset=123)
    registry_key.AddValue(registry_value)

    value_data = u'2592000'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'CriticalSectionTimeout', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=153)
    registry_key.AddValue(registry_value)

    value_data = u'\x00'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ExcludeFromKnownDlls', data=value_data,
        data_type=dfwinreg_definitions.REG_MULTI_SZ, offset=163)
    registry_key.AddValue(registry_value)

    value_data = u'0'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'GlobalFlag', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=173)
    registry_key.AddValue(registry_value)

    value_data = u'0'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'HeapDeCommitFreeBlockThreshold', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=183)
    registry_key.AddValue(registry_value)

    value_data = u'0'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'HeapDeCommitTotalFreeThreshold', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=203)
    registry_key.AddValue(registry_value)

    value_data = u'0'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'HeapSegmentCommit', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=213)
    registry_key.AddValue(registry_value)

    value_data = u'0'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'HeapSegmentReserve', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=223)
    registry_key.AddValue(registry_value)

    value_data = u'2'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'NumberOfInitialSessions', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=243)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\Session Manager')
    time_string = u'2012-08-31 20:45:29'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = lfu.BootExecutePlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] BootExecute: autocheck autochk *').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    expected_message = (
        u'[{0:s}] '
        u'CriticalSectionTimeout: 2592000 '
        u'ExcludeFromKnownDlls: [] '
        u'GlobalFlag: 0 '
        u'HeapDeCommitFreeBlockThreshold: 0 '
        u'HeapDeCommitTotalFreeThreshold: 0 '
        u'HeapSegmentCommit: 0 '
        u'HeapSegmentReserve: 0 '
        u'NumberOfInitialSessions: 2').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

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
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'BootVerificationProgram', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    value_data = u'C:\\WINDOWS\\system32\\googleupdater.exe'.encode(
        u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ImagePath', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=123)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = u'\\ControlSet001\\Control\\BootVerificationProgram'
    time_string = u'2012-08-31 20:45:29'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = lfu.BootVerificationPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'ImagePath: C:\\WINDOWS\\system32\\googleupdater.exe').format(
            key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
