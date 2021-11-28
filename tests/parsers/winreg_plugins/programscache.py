#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Explorer ProgramsCache Windows Registry plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.winreg_plugins import programscache

from tests.parsers.winreg_plugins import test_lib


class ExplorerProgramCacheWindowsRegistryPluginTest(
    test_lib.RegistryPluginTestCase):
  """Tests for the Explorer ProgramsCache Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = programscache.ExplorerProgramsCacheWindowsRegistryPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\StartPage')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\StartPage2')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcessStartPage(self):
    """Tests the Process function on a StartPage key."""
    test_file_entry = self._GetTestFileEntry(['NTUSER.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\StartPage')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = programscache.ExplorerProgramsCacheWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 77)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # The ProgramsCache entry shell item event.
    expected_event_values = {
        'date_time': '2009-08-04 15:12:24',
        'data_type': 'windows:shell_item:file_entry',
        'localized_name': '@shell32.dll,-21782',
        'long_name': 'Programs',
        'name': 'Programs',
        'origin': '{0:s} ProgramsCache'.format(key_path),
        'parser': 'explorer_programscache/shell_items',
        'shell_item_path': 'Programs',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # The ProgramsCache list event.
    expected_entries = (
        '0: Programs '
        '1: Internet Explorer.lnk '
        '2: Outlook Express.lnk '
        '3: Remote Assistance.lnk '
        '4: Windows Media Player.lnk '
        '5: Programs Accessories '
        '6: Address Book.lnk '
        '7: Command Prompt.lnk '
        '8: Notepad.lnk '
        '9: Program Compatibility Wizard.lnk '
        '10: Synchronize.lnk '
        '11: Tour Windows XP.lnk '
        '12: Windows Explorer.lnk '
        '13: Programs Accessories\\Accessibility '
        '14: Magnifier.lnk '
        '15: Narrator.lnk '
        '16: On-Screen Keyboard.lnk '
        '17: Utility Manager.lnk '
        '18: Programs Accessories\\System Tools '
        '19: Internet Explorer (No Add-ons).lnk')

    expected_event_values = {
        'date_time': '2009-08-04 15:22:18.4196250',
        'data_type': 'windows:registry:explorer:programcache',
        'entries': expected_entries,
        'key_path': key_path,
        'parser': 'explorer_programscache',
        'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}

    self.CheckEventValues(storage_writer, events[75], expected_event_values)

    # The Windows Registry key event.
    expected_values = (
        'Favorites: [REG_BINARY] (55 bytes) '
        'FavoritesChanges: [REG_DWORD_LE] 1 '
        'FavoritesResolve: [REG_BINARY] (8 bytes) '
        'StartMenu_Balloon_Time: [REG_BINARY] (8 bytes) '
        'StartMenu_Start_Time: [REG_BINARY] (8 bytes)')

    expected_event_values = {
        'date_time': '2009-08-04 15:22:18.4196250',
        'data_type': 'windows:registry:key_value',
        'key_path': key_path,
        'parser': 'explorer_programscache',
        'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
        'values': expected_values}

    self.CheckEventValues(storage_writer, events[76], expected_event_values)

  def testProcessStartPage2(self):
    """Tests the Process function on a StartPage2 key."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\StartPage2')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = programscache.ExplorerProgramsCacheWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 118)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2010-11-10 07:50:38',
        'data_type': 'windows:shell_item:file_entry',
        'origin': '{0:s} ProgramsCache'.format(key_path),
        'parser': 'explorer_programscache/shell_items',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
