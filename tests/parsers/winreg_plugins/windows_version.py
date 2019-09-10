#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the WinVer Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.winreg_plugins import windows_version

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class WindowsRegistryInstallationEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows installation event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_version.WindowsRegistryInstallationEventData()

    expected_attribute_names = [
        'build_number', 'data_type', 'key_path', 'offset', 'owner',
        'product_name', 'query', 'service_pack', 'version']

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
    time_string = '2012-08-31 20:09:55.123521'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = windows_version.WindowsVersionPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-08-31 20:09:55.123521')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_data.parser, plugin.plugin_name)

    self.assertEqual(event_data.data_type, 'windows:registry:key_value')

    expected_message = (
        '[{0:s}] '
        'CSDVersion: [REG_SZ] Service Pack 1 '
        'CurrentVersion: [REG_SZ] 5.1 '
        'ProductName: [REG_SZ] MyTestOS '
        'RegisteredOwner: [REG_SZ] A Concerned Citizen').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2012-08-31 20:09:55.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_INSTALLATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.data_type, 'windows:registry:installation')
    self.assertEqual(event_data.key_path, key_path)
    self.assertEqual(event_data.owner, 'A Concerned Citizen')
    self.assertEqual(event_data.product_name, 'MyTestOS')
    self.assertEqual(event_data.service_pack, 'Service Pack 1')
    self.assertEqual(event_data.version, '5.1')

    expected_message = (
        'MyTestOS 5.1 Service Pack 1 '
        'Owner: A Concerned Citizen '
        'Origin: {0:s}').format(key_path)
    expected_short_message = (
        'MyTestOS 5.1 Service Pack 1 '
        'Origin: HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Win...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-03-15 07:09:20.671875')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_data.parser, plugin.plugin_name)

    self.assertEqual(event_data.data_type, 'windows:registry:key_value')

    expected_message = (
        '[{0:s}] '
        'BuildGUID: [REG_SZ] f4bf21b9-55fe-4ee8-a84b-0e91cbd5fe5d '
        'BuildLab: [REG_SZ] 7601.win7sp1_gdr.111118-2330 '
        'BuildLabEx: [REG_SZ] 7601.17727.amd64fre.win7sp1_gdr.111118-2330 '
        'CSDBuildNumber: [REG_SZ] 1130 '
        'CSDVersion: [REG_SZ] Service Pack 1 '
        'CurrentBuild: [REG_SZ] 7601 '
        'CurrentBuildNumber: [REG_SZ] 7601 '
        'CurrentType: [REG_SZ] Multiprocessor Free '
        'CurrentVersion: [REG_SZ] 6.1 '
        'DigitalProductId: [REG_BINARY] (164 bytes) '
        'DigitalProductId4: [REG_BINARY] (1272 bytes) '
        'EditionID: [REG_SZ] Ultimate '
        'InstallationType: [REG_SZ] Client '
        'PathName: [REG_SZ] C:\\Windows '
        'ProductId: [REG_SZ] 00426-065-0381817-86216 '
        'ProductName: [REG_SZ] Windows 7 Ultimate '
        'RegisteredOrganization: [REG_SZ]  '
        'RegisteredOwner: [REG_SZ] Windows User '
        'SoftwareType: [REG_SZ] System '
        'SystemRoot: [REG_SZ] C:\\Windows').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
