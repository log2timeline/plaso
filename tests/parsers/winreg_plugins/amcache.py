#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the AMCache Registry plugin."""

import unittest

from dfwinreg import regf as dfwinreg_regf

from plaso.parsers.winreg_plugins import amcache

from tests.parsers.winreg_plugins import test_lib


class AMCachePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the AMCache.hve Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = amcache.AMCachePlugin()

    self._AssertFiltersOnKeyPath(plugin, '\\Root')
    self._AssertNotFiltersOnKeyPath(plugin, '\\Root\\File')
    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['Amcache.hve'])

    file_object = test_file_entry.GetFileObject()

    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage='cp1252', emulate_virtual_keys=False)
    registry_file.Open(file_object)

    registry_key = registry_file.GetKeyByPath('\\Root')

    plugin = amcache.AMCachePlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3497)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_full_path = (
        'c:\\users\\user\\appdata\\local\\temp\\chocolatey\\'
        'is-f4510.tmp\\idafree50.tmp')

    expected_event_values = {
        'data_type': 'windows:registry:amcache',
        'file_creation_time': '2017-08-01T12:43:35.1772758+00:00',
        'file_modification_time': '2017-08-01T12:43:35.3024523+00:00',
        'full_path': expected_full_path,
        'installation_time': None,
        'last_written_time': '2017-08-01T12:43:35.3715211+00:00',
        'link_time': '1992-06-19T22:22:17+00:00',
        'msi_installation_time': None,
        'sha1': '82274eef0911a948f91425f5e5b0e730517fe75e'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1420)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'windows:registry:amcache:programs',
        'entry_type': 'AddRemoveProgram',
        'file_paths': [
            'c:\\program files (x86)\\fileinsight\\plugins',
            'c:\\program files (x86)\\fileinsight\\plugins\\anomaly chart',
            'c:\\program files (x86)\\fileinsight'],
        'installation_time': '2017-08-01T12:52:59+00:00',
        'name': 'FileInsight - File analysis tool',
        'publisher': 'McAfee Inc.',
        'uninstall_key': [
            'HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\Microsoft\\Windows\\'
            'CurrentVersion\\Uninstall\\FileInsight']}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3480)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWindows101(self):
    """Tests the Process function on a Windows 10 1807 AMCache.hve file."""
    test_file_entry = self._GetTestFileEntry(['win10-Amcache.hve'])

    file_object = test_file_entry.GetFileObject()

    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage='cp1252', emulate_virtual_keys=False)
    registry_file.Open(file_object)

    registry_key = registry_file.GetKeyByPath('\\Root')

    plugin = amcache.AMCachePlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 236)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:registry:amcache',
        'file_creation_time': None,
        'file_modification_time': None,
        'full_path': 'c:\\windows\\system32\\svchost.exe',
        'installation_time': None,
        'last_written_time': None,
        'link_time': '1997-01-10T22:26:24+00:00',
        'msi_installation_time': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 135)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
