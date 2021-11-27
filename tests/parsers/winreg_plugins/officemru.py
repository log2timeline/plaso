#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Office MRUs Windows Registry plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.winreg_plugins import officemru

from tests.parsers.winreg_plugins import test_lib


class OfficeMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Microsoft Office MRUs Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = officemru.OfficeMRUPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Access\\File MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Access\\Place MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Excel\\File MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Excel\\Place MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'PowerPoint\\File MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'PowerPoint\\Place MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Word\\File MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Word\\Place MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\Word\\'
        'File MRU')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = officemru.OfficeMRUPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2012-03-13 18:27:15.0898020',
        'data_type': 'windows:registry:office_mru_list',
        'entries': (
            'Item 1: [F00000000][T01CD0146EA1EADB0][O00000000]*'
            'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\'
            'SA-23E Mitchell-Hyundyne Starfury.docx '
            'Item 2: [F00000000][T01CD00921FC127F0][O00000000]*'
            'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\Earthforce '
            'SA-26 Thunderbolt Star Fury.docx '
            'Item 3: [F00000000][T01CD009208780140][O00000000]*'
            'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\StarFury.docx '
            'Item 4: [F00000000][T01CCFE0B22DA9EF0][O00000000]*'
            'C:\\Users\\nfury\\Documents\\VIBRANIUM.docx '
            'Item 5: [F00000000][T01CCFCBA595DFC30][O00000000]*'
            'C:\\Users\\nfury\\Documents\\ADAMANTIUM-Background.docx'),
        # This should just be the plugin name, as we're invoking it directly,
        # and not through the parser.
        'parser': plugin.NAME,
        'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    # Test OfficeMRUWindowsRegistryEvent.
    expected_value_string = (
        '[F00000000][T01CD0146EA1EADB0][O00000000]*'
        'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\'
        'SA-23E Mitchell-Hyundyne Starfury.docx')

    expected_event_values = {
        'date_time': '2012-03-13 18:27:15.0830000',
        'data_type': 'windows:registry:office_mru',
        'key_path': key_path,
        'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
        'value_string': expected_value_string}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
