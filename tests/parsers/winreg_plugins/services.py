#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains tests for Services Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import services

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class ServicesRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Services Windows Registry plugin."""

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

    plugin = services.ServicesPlugin()
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
        u'DisplayName: Test Driver '
        u'DriverPackageId: testdriver.inf_x86_neutral_dd39b6b0a45226c4 '
        u'ErrorControl: Normal (1) '
        u'Group: Pnp Filter '
        u'ImagePath: C:\\Dell\\testdriver.sys '
        u'Start: Auto Start (2) '
        u'Type: File System Driver (0x2)').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testProcessFile(self):
    """Tests the Process function on a key in a file."""
    test_file_entry = self._GetTestFileEntry([u'SYSTEM'])
    key_path = u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\services'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    events = []

    # Select a few service subkeys to perform additional testing.
    bits_events = None
    mc_task_manager_events = None
    rdp_video_miniport_events = None

    plugin = services.ServicesPlugin()
    for winreg_subkey in registry_key.GetSubkeys():
      storage_writer = self._ParseKeyWithPlugin(
          winreg_subkey, plugin, file_entry=test_file_entry)

      events_subkey = list(storage_writer.GetEvents())

      events.extend(list(events_subkey))

      if winreg_subkey.name == u'BITS':
        bits_events = events_subkey
      elif winreg_subkey.name == u'McTaskManager':
        mc_task_manager_events = events_subkey
      elif winreg_subkey.name == u'RdpVideoMiniport':
        rdp_video_miniport_events = events_subkey

    self.assertEqual(len(events), 416)

    # Test the BITS subkey events.
    self.assertEqual(len(bits_events), 1)

    event = bits_events[0]

    self.assertEqual(event.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-06 20:43:27.639075')
    self.assertEqual(event.timestamp, expected_timestamp)

    self._TestRegvalue(event, u'Type', 0x20)
    self._TestRegvalue(event, u'Start', 3)
    self._TestRegvalue(
        event, u'ServiceDll', u'%SystemRoot%\\System32\\qmgr.dll')

    # Test the McTaskManager subkey events.
    self.assertEqual(len(mc_task_manager_events), 1)

    event = mc_task_manager_events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-09-16 20:49:16.877415')
    self.assertEqual(event.timestamp, expected_timestamp)

    self._TestRegvalue(event, u'DisplayName', u'McAfee Task Manager')
    self._TestRegvalue(event, u'Type', 0x10)

    # Test the RdpVideoMiniport subkey events.
    self.assertEqual(len(rdp_video_miniport_events), 1)

    event = rdp_video_miniport_events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-09-17 13:37:59.347157')
    self.assertEqual(event.timestamp, expected_timestamp)

    self._TestRegvalue(event, u'Start', 3)
    expected_value = u'System32\\drivers\\rdpvideominiport.sys'
    self._TestRegvalue(event, u'ImagePath', expected_value)


if __name__ == '__main__':
  unittest.main()
