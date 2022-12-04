#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the CCleaner Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import ccleaner

from tests.parsers.winreg_plugins import test_lib


class CCleanerRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the CCleaner Windows Registry plugin."""

  # TODO: add tests for _ParseUpdateKeyValue

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = ccleaner.CCleanerPlugin()

    key_path = 'HKEY_CURRENT_USER\\Software\\Piriform\\CCleaner'
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    plugin = ccleaner.CCleanerPlugin()
    test_file_entry = self._GetTestFileEntry(['NTUSER-CCLEANER.DAT'])
    key_path = 'HKEY_CURRENT_USER\\Software\\Piriform\\CCleaner'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
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
        'data_type': 'ccleaner:update',
        'key_path': key_path,
        'update_time': '2013-07-13T10:03:14'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_configuration = (
        '(App)Cookies: True '
        '(App)Delete Index.dat files: True '
        '(App)History: True '
        '(App)Last Download Location: True '
        '(App)Other Explorer MRUs: True '
        '(App)Recent Documents: True '
        '(App)Recently Typed URLs: True '
        '(App)Run (in Start Menu): True '
        '(App)Temporary Internet Files: True '
        '(App)Thumbnail Cache: True '
        'CookiesToSave: *.piriform.com '
        'WINDOW_HEIGHT: 524 '
        'WINDOW_LEFT: 146 '
        'WINDOW_MAX: 0 '
        'WINDOW_TOP: 102 '
        'WINDOW_WIDTH: 733')

    expected_event_values = {
        'configuration': expected_configuration,
        'data_type': 'ccleaner:configuration',
        'key_path': key_path,
        'last_written_time': '2013-07-13T14:03:26.8616882+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
