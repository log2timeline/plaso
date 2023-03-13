#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the WinVer Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import windows_version

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class WindowsRegistryInstallationEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows installation event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_version.WindowsRegistryInstallationEventData()

    expected_attribute_names = [
        '_event_data_stream_identifier',
        '_event_values_hash',
        '_parser_chain',
        'build_number',
        'data_type',
        'installation_time',
        'key_path',
        'owner',
        'product_name',
        'service_pack',
        'version']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsVersionPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Windows version Windows Registry plugin."""

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
        'CurrentVersion', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    value_data = 'Service Pack 1'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'CSDVersion', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=1892)
    registry_key.AddValue(registry_value)

    value_data = '5.1'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'CurrentVersion', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=1121)
    registry_key.AddValue(registry_value)

    value_data = b'\x13\x1aAP'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'InstallDate', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_LITTLE_ENDIAN, offset=1001)
    registry_key.AddValue(registry_value)

    value_data = 'MyTestOS'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ProductName', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=123)
    registry_key.AddValue(registry_value)

    value_data = 'A Concerned Citizen'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'RegisteredOwner', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ, offset=612)
    registry_key.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = windows_version.WindowsVersionPlugin()

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
    registry_key = self._CreateTestKey(key_path, '2012-08-31 20:09:55.123521')

    plugin = windows_version.WindowsVersionPlugin()
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
        'data_type': 'windows:registry:installation',
        'installation_time': '2012-08-31T20:09:55+00:00',
        'key_path': key_path,
        'owner': 'A Concerned Citizen',
        'product_name': 'MyTestOS',
        'service_pack': 'Service Pack 1',
        'version': '5.1'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'windows:registry:key_value',
        'key_path': key_path,
        'last_written_time': '2012-08-31T20:09:55.1235210+00:00',
        'values': [
            ('CSDVersion', 'REG_SZ', 'Service Pack 1'),
            ('CurrentVersion', 'REG_SZ', '5.1'),
            ('ProductName', 'REG_SZ', 'MyTestOS'),
            ('RegisteredOwner', 'REG_SZ', 'A Concerned Citizen')]}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessFile(self):
    """Tests the Process function on a Windows Registry file."""
    test_file_entry = self._GetTestFileEntry(['SOFTWARE-RunTests'])
    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = windows_version.WindowsVersionPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

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
        'data_type': 'windows:registry:installation',
        'installation_time': '2010-11-10T17:10:57+00:00',
        'key_path': key_path,
        'owner': 'Windows User',
        'product_name': 'Windows 7 Ultimate',
        'service_pack': 'Service Pack 1',
        'version': '6.1'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
