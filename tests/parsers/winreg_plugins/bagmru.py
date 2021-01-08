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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 15)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'windows:registry:bagmru',
        'entries': (
            'Index: 1 [MRU Value 0]: Shell item path: <My Computer>'),
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.plugin_name,
        'timestamp': '2009-08-04 15:19:16.997750'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'entries': (
            'Index: 1 [MRU Value 0]: Shell item path: <My Computer> C:\\'),
        'timestamp': '2009-08-04 15:19:10.669625'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'key_path': '{0:s}\\0\\0\\0\\0\\0'.format(key_path),
        'timestamp': '2009-08-04 15:19:16.997750'}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)


if __name__ == '__main__':
  unittest.main()
