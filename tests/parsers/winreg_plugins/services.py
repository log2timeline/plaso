#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This file contains tests for Services Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import services

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
    filetime.CopyFromDateTimeString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'TestDriver', key_path=key_path, last_written_time=filetime.timestamp,
        offset=1456)

    value_data = b'\x02\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Type', data=value_data, data_type=dfwinreg_definitions.REG_DWORD,
        offset=123)
    registry_key.AddValue(registry_value)

    value_data = b'\x02\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Start', data=value_data, data_type=dfwinreg_definitions.REG_DWORD,
        offset=127)
    registry_key.AddValue(registry_value)

    value_data = b'\x01\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ErrorControl', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD, offset=131)
    registry_key.AddValue(registry_value)

    value_data = 'Pnp Filter'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Group', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=140)
    registry_key.AddValue(registry_value)

    value_data = 'Test Driver'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DisplayName', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=160)
    registry_key.AddValue(registry_value)

    value_data = 'testdriver.inf_x86_neutral_dd39b6b0a45226c4'.encode(
        'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DriverPackageId', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=180)
    registry_key.AddValue(registry_value)

    value_data = 'C:\\Dell\\testdriver.sys'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ImagePath', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=200)
    registry_key.AddValue(registry_value)

    return registry_key

  # TODO: add test for _GetServiceDll
  # TODO: add test for _GetValuesFromKey

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = services.ServicesPlugin()

    # TODO: add test.

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function on a virtual key."""
    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\services\\TestDriver'
    registry_key = self._CreateTestKey(key_path, '2012-08-28 09:23:49.002031')

    plugin = services.ServicesPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_values = (
        'DisplayName: [REG_SZ] Test Driver '
        'DriverPackageId: [REG_SZ] testdriver.inf_x86_neutral_dd39b6b0a45226c4 '
        'Group: [REG_SZ] Pnp Filter')

    expected_event_values = {
        'date_time': '2012-08-28 09:23:49.0020310',
        'data_type': 'windows:registry:service',
        'error_control': 1,
        'image_path': 'C:\\Dell\\testdriver.sys',
        'key_path': key_path,
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.NAME,
        'service_type': 2,
        'start_type': 2,
        'values': expected_values}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testProcessFile(self):
    """Tests the Process function on a key in a file."""
    test_file_entry = self._GetTestFileEntry(['SYSTEM'])
    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\services'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = services.ServicesPlugin()

    events = []
    for winreg_subkey in registry_key.GetSubkeys():
      storage_writer = self._ParseKeyWithPlugin(
          winreg_subkey, plugin, file_entry=test_file_entry)

      events_subkey = list(storage_writer.GetEvents())
      events.extend(events_subkey)

    self.assertEqual(len(events), 416)

    # Test the BITS subkey events.
    winreg_subkey = registry_key.GetSubkeyByName('BITS')
    bits_storage_writer = self._ParseKeyWithPlugin(
        winreg_subkey, plugin, file_entry=test_file_entry)
    bits_events = list(bits_storage_writer.GetEvents())

    self.assertEqual(len(bits_events), 1)

    expected_event_values = {
        'date_time': '2012-04-06 20:43:27.6390752',
        'data_type': 'windows:registry:service',
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.NAME,
        'service_dll': '%SystemRoot%\\System32\\qmgr.dll',
        'service_type': 0x20,
        'start_type': 3}

    self.CheckEventValues(
        bits_storage_writer, bits_events[0], expected_event_values)

    # Test the McTaskManager subkey events.
    winreg_subkey = registry_key.GetSubkeyByName('McTaskManager')
    mc_task_manager_storage_writer = self._ParseKeyWithPlugin(
        winreg_subkey, plugin, file_entry=test_file_entry)
    mc_task_manager_events = list(mc_task_manager_storage_writer.GetEvents())

    self.assertEqual(len(mc_task_manager_events), 1)

    expected_event_values = {
        'date_time': '2011-09-16 20:49:16.8774156',
        'data_type': 'windows:registry:service',
        'service_type': 0x10}

    self.CheckEventValues(
        mc_task_manager_storage_writer, mc_task_manager_events[0],
        expected_event_values)

    event_data = self._GetEventDataOfEvent(
        mc_task_manager_storage_writer, mc_task_manager_events[0])
    self.assertTrue(
        'DisplayName: [REG_SZ] McAfee Task Manager' in event_data.values)

    # Test the RdpVideoMiniport subkey events.
    winreg_subkey = registry_key.GetSubkeyByName('RdpVideoMiniport')
    rdp_video_miniport_storage_writer = self._ParseKeyWithPlugin(
        winreg_subkey, plugin, file_entry=test_file_entry)
    rdp_video_miniport_events = list(
        rdp_video_miniport_storage_writer.GetEvents())

    self.assertEqual(len(rdp_video_miniport_events), 1)

    expected_event_values = {
        'date_time': '2011-09-17 13:37:59.3471577',
        'data_type': 'windows:registry:service',
        'image_path': 'System32\\drivers\\rdpvideominiport.sys',
        'start_type': 3}

    self.CheckEventValues(
        rdp_video_miniport_storage_writer, rdp_video_miniport_events[0],
        expected_event_values)


if __name__ == '__main__':
  unittest.main()
