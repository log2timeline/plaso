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
        'data_type': 'windows:registry:service',
        'error_control': 1,
        'image_path': 'C:\\Dell\\testdriver.sys',
        'key_path': key_path,
        'last_written_time': '2012-08-28T09:23:49.0020310+00:00',
        'service_type': 2,
        'start_type': 2,
        'values': [
            ('Group', 'REG_SZ', 'Pnp Filter'),
            ('DisplayName', 'REG_SZ', 'Test Driver'),
            ('DriverPackageId', 'REG_SZ',
             'testdriver.inf_x86_neutral_dd39b6b0a45226c4')]}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessFile(self):
    """Tests the Process function on a key in a file."""
    test_file_entry = self._GetTestFileEntry(['SYSTEM'])
    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\services\\BITS'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = services.ServicesPlugin()
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
        'data_type': 'windows:registry:service',
        'last_written_time': '2012-04-06T20:43:27.6390752+00:00',
        'service_dll': '%SystemRoot%\\System32\\qmgr.dll',
        'service_type': 0x20,
        'start_type': 3}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
