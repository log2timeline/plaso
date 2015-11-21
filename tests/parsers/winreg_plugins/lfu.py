#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Less Frequently Used (LFU) Windows Registry plugin."""

import unittest

from plaso.dfwinreg import definitions as dfwinreg_definitions
from plaso.dfwinreg import fake as dfwinreg_fake
from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import lfu

from tests.parsers.winreg_plugins import test_lib


class TestBootExecutePlugin(test_lib.RegistryPluginTestCase):
  """Tests for the LFU BootExecute Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = lfu.BootExecutePlugin()

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

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, registry_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] BootExecute: autocheck autochk *').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    event_object = event_objects[1]

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
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


class TestBootVerificationRegistry(test_lib.RegistryPluginTestCase):
  """Tests for the LFU BootVerification Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = lfu.BootVerificationPlugin()

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

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, registry_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'ImagePath: C:\\WINDOWS\\system32\\googleupdater.exe').format(
            key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
