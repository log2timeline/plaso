#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the WinVer Windows Registry plugin."""

import unittest

from plaso.dfwinreg import definitions as dfwinreg_definitions
from plaso.dfwinreg import fake as dfwinreg_fake
from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import winver

from tests.parsers.winreg_plugins import test_lib


class WinVerPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the WinVer Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = winver.WinVerPlugin()

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
        u'CurrentVersion', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    value_data = u'Service Pack 1'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'CSDVersion', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=1892)
    registry_key.AddValue(registry_value)

    value_data = u'5.1'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'CurrentVersion', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=1121)
    registry_key.AddValue(registry_value)

    value_data = b'\x13\x1aAP'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'InstallDate', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_LITTLE_ENDIAN, offset=1001)
    registry_key.AddValue(registry_value)

    value_data = u'MyTestOS'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ProductName', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=123)
    registry_key.AddValue(registry_value)

    value_data = u'A Concerned Citizen'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'RegisteredOwner', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=612)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
    time_string = u'2012-08-31 20:09:55.123521'
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

    expected_data_type = 'windows:registry:key_value'
    self.assertEqual(event_object.data_type, expected_data_type)

    expected_message = (
        u'[{0:s}] '
        u'Owner: A Concerned Citizen '
        u'Product name: MyTestOS '
        u'Service pack: Service Pack 1 '
        u'Windows Version Information: 5.1').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    event_object = event_objects[1]
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.INSTALLATION_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-08-31 20:09:55')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.data_type, 'windows:registry:installation')

    expected_data_type = 'windows:registry:installation'
    self.assertEqual(event_object.data_type, expected_data_type)

    expected_message = (
        u'MyTestOS 5.1 Service Pack 1 '
        u'Owner: owner '
        u'Origin: {0:s}').format(key_path)
    expected_short_message = (
        u'MyTestOS 5.1 Service Pack 1 '
        u'Origin: HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Win...')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

  def testProcessFile(self):
    """Tests the Process function on a Windows Registry file."""
    test_file_entry = self._GetTestFileEntryFromPath([u'SOFTWARE-RunTests'])
    key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-15 07:09:20.671875')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.data_type, 'windows:registry:key_value')

    expected_message = (
        u'[{0:s}] '
        u'Owner: Windows User '
        u'Product name: Windows 7 Ultimate '
        u'Service pack: Service Pack 1 '
        u'Windows Version Information: 6.1').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
