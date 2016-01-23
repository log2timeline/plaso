#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains tests for Services Windows Registry plugin."""

import unittest

from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake
from dfwinreg import filetime as dfwinreg_filetime

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import services

from tests.parsers.winreg_plugins import test_lib


class ServicesRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """The unit test for Services Windows Registry plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = services.ServicesPlugin()

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path: the Windows Registry key path.
      time_string: string containing the key last written date and time.

    Returns:
      A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    filetime = dfwinreg_filetime.Filetime()
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'TestDriver', key_path=key_path, last_written_time=filetime.timestamp,
        offset=1456)

    value_data = b'\x02\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Type', data=value_data, data_type=dfwinreg_definitions.REG_DWORD,
        offset=123)
    registry_key.AddValue(registry_value)

    value_data = b'\x02\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Start', data=value_data, data_type=dfwinreg_definitions.REG_DWORD,
        offset=127)
    registry_key.AddValue(registry_value)

    value_data = b'\x01\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ErrorControl', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD, offset=131)
    registry_key.AddValue(registry_value)

    value_data = u'Pnp Filter'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Group', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=140)
    registry_key.AddValue(registry_value)

    value_data = u'Test Driver'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DisplayName', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=160)
    registry_key.AddValue(registry_value)

    value_data = u'testdriver.inf_x86_neutral_dd39b6b0a45226c4'.encode(
        u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DriverPackageId', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=180)
    registry_key.AddValue(registry_value)

    value_data = u'C:\\Dell\\testdriver.sys'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ImagePath', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=200)
    registry_key.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function on a virtual key."""
    key_path = (
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\services\\TestDriver')
    time_string = u'2012-08-28 09:23:49.002031'
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
        u'DisplayName: Test Driver '
        u'DriverPackageId: testdriver.inf_x86_neutral_dd39b6b0a45226c4 '
        u'ErrorControl: Normal (1) '
        u'Group: Pnp Filter '
        u'ImagePath: C:\\Dell\\testdriver.sys '
        u'Start: Auto Start (2) '
        u'Type: File System Driver (0x2)').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

  def testProcessFile(self):
    """Tests the Process function on a key in a file."""
    test_file_entry = self._GetTestFileEntryFromPath([u'SYSTEM'])
    key_path = u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\services'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    event_objects = []

    # Select a few service subkeys to perform additional testing.
    bits_event_objects = None
    mc_task_manager_event_objects = None
    rdp_video_miniport_event_objects = None

    for winreg_subkey in registry_key.GetSubkeys():
      event_queue_consumer = self._ParseKeyWithPlugin(
          self._plugin, winreg_subkey, file_entry=test_file_entry)
      sub_event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

      event_objects.extend(sub_event_objects)

      if winreg_subkey.name == u'BITS':
        bits_event_objects = sub_event_objects
      elif winreg_subkey.name == u'McTaskManager':
        mc_task_manager_event_objects = sub_event_objects
      elif winreg_subkey.name == u'RdpVideoMiniport':
        rdp_video_miniport_event_objects = sub_event_objects

    self.assertEqual(len(event_objects), 416)

    # Test the BITS subkey event objects.
    self.assertEqual(len(bits_event_objects), 1)

    event_object = bits_event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-06 20:43:27.639075')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self._TestRegvalue(event_object, u'Type', 0x20)
    self._TestRegvalue(event_object, u'Start', 3)
    self._TestRegvalue(
        event_object, u'ServiceDll', u'%SystemRoot%\\System32\\qmgr.dll')

    # Test the McTaskManager subkey event objects.
    self.assertEqual(len(mc_task_manager_event_objects), 1)

    event_object = mc_task_manager_event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-09-16 20:49:16.877415')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self._TestRegvalue(event_object, u'DisplayName', u'McAfee Task Manager')
    self._TestRegvalue(event_object, u'Type', 0x10)

    # Test the RdpVideoMiniport subkey event objects.
    self.assertEqual(len(rdp_video_miniport_event_objects), 1)

    event_object = rdp_video_miniport_event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-09-17 13:37:59.347157')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self._TestRegvalue(event_object, u'Start', 3)
    expected_value = u'System32\\drivers\\rdpvideominiport.sys'
    self._TestRegvalue(event_object, u'ImagePath', expected_value)


if __name__ == '__main__':
  unittest.main()
