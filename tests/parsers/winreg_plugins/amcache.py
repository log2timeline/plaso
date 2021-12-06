#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the AMCache Registry plugin."""

import unittest

from dfwinreg import regf as dfwinreg_regf

from plaso.lib import definitions
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

    # 1178 windows:registry:amcache events
    # 2105 last written time events
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3283)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_full_path = (
        'c:\\users\\user\\appdata\\local\\temp\\chocolatey\\'
        'is-f4510.tmp\\idafree50.tmp')

    expected_event_values = {
        'data_type': 'windows:registry:amcache',
        'date_time': '1992-06-19 22:22:17',
        'full_path': expected_full_path,
        'sha1': '82274eef0911a948f91425f5e5b0e730517fe75e',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LINK_TIME}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'windows:registry:amcache:programs',
        'date_time': '2017-08-01 12:52:59',
        'entry_type': 'AddRemoveProgram',
        'file_paths': [
            'c:\\program files (x86)\\fileinsight\\plugins',
            'c:\\program files (x86)\\fileinsight\\plugins\\anomaly chart',
            'c:\\program files (x86)\\fileinsight'],
        'name': 'FileInsight - File analysis tool',
        'publisher': 'McAfee Inc.',
        'timestamp_desc': definitions.TIME_DESCRIPTION_INSTALLATION,
        'uninstall_key': [
            'HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\Microsoft\\Windows\\'
            'CurrentVersion\\Uninstall\\FileInsight']}

    self.CheckEventValues(storage_writer, events[1285], expected_event_values)

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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 236)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'windows:registry:amcache',
        'date_time': '1997-01-10 22:26:24',
        'full_path': 'c:\\windows\\system32\\svchost.exe',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LINK_TIME}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
