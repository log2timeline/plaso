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

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    self.assertEqual(event.data_type, 'windows:registry:key_value')
    self.CheckTimestamp(event.timestamp, '2012-08-31 20:09:55.123521')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    expected_message = (
        '[{0:s}] '
        'CSDVersion: Service Pack 1 '
        'CurrentVersion: 5.1 '
        'ProductName: MyTestOS '
        'RegisteredOwner: A Concerned Citizen').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    self.assertEqual(event.data_type, 'windows:registry:installation')
    self.CheckTimestamp(event.timestamp, '2012-08-31 20:09:55.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_INSTALLATION)

    self.assertEqual(event.key_path, key_path)
    self.assertEqual(event.owner, 'A Concerned Citizen')
    self.assertEqual(event.product_name, 'MyTestOS')
    self.assertEqual(event.service_pack, 'Service Pack 1')
    self.assertEqual(event.version, '5.1')

    expected_message = (
        'MyTestOS 5.1 Service Pack 1 '
        'Owner: A Concerned Citizen '
        'Origin: {0:s}').format(key_path)
    expected_short_message = (
        'MyTestOS 5.1 Service Pack 1 '
        'Origin: HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Win...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

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

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    self.assertEqual(event.data_type, 'windows:registry:key_value')
    self.CheckTimestamp(event.timestamp, '2012-03-15 07:09:20.671875')

    expected_message = (
        '[{0:s}] '
        'BuildGUID: f4bf21b9-55fe-4ee8-a84b-0e91cbd5fe5d '
        'BuildLab: 7601.win7sp1_gdr.111118-2330 '
        'BuildLabEx: 7601.17727.amd64fre.win7sp1_gdr.111118-2330 '
        'CSDBuildNumber: 1130 '
        'CSDVersion: Service Pack 1 '
        'CurrentBuild: 7601 '
        'CurrentBuildNumber: 7601 '
        'CurrentType: Multiprocessor Free '
        'CurrentVersion: 6.1 '
        'DigitalProductId: (binary) '
        'DigitalProductId4: (binary) '
        'EditionID: Ultimate '
        'InstallationType: Client '
        'PathName: C:\\Windows '
        'ProductId: 00426-065-0381817-86216 '
        'ProductName: Windows 7 Ultimate '
        'RegisteredOrganization:  '
        'RegisteredOwner: Windows User '
        'SoftwareType: System '
        'SystemRoot: C:\\Windows').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
