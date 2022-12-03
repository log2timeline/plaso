#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the BagMRU Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import bagmru

from tests.parsers.winreg_plugins import test_lib


class TestBagMRUWindowsRegistryPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the BagMRU plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = bagmru.BagMRUWindowsRegistryPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\ShellNoRoam\\'
        'BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\'
        'Microsoft\\Windows\\Shell\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\'
        'Microsoft\\Windows\\ShellNoRoam\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Local Settings\\Software\\Microsoft\\Windows\\'
        'Shell\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Local Settings\\Software\\Microsoft\\Windows\\'
        'ShellNoRoam\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    plugin = bagmru.BagMRUWindowsRegistryPlugin()
    test_file_entry = self._GetTestFileEntry(['NTUSER.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:registry:bagmru',
        'entries': 'Index: 1 [MRU Value 0]: Shell item path: <My Computer>',
        'key_path': key_path,
        'last_written_time': '2009-08-04T15:19:16.9977500+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'windows:registry:bagmru',
        'entries': (
            'Index: 1 [MRU Value 0]: Shell item path: <My Computer> C:\\'),
        'key_path': '{0:s}\\0'.format(key_path),
        'last_written_time': '2009-08-04T15:19:10.6696250+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'windows:registry:bagmru',
        'entries': None,
        'key_path': '{0:s}\\0\\0\\0\\0\\0'.format(key_path),
        'last_written_time': '2009-08-04T15:19:16.9977500+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
