#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Explorer ProgramsCache Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 77)

    events = list(storage_writer.GetEvents())

    # The ProgramsCache entry shell item event.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2009-08-04 15:12:24.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.parser, 'explorer_programscache/shell_items')
    self.assertEqual(event_data.data_type, 'windows:shell_item:file_entry')

    expected_message = (
        'Name: Programs '
        'Long name: Programs '
        'Localized name: @shell32.dll,-21782 '
        'Shell item path: Programs '
        'Origin: {0:s} ProgramsCache').format(key_path)
    expected_short_message = (
        'Name: Programs '
        'Origin: HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\'
        'CurrentVe...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # The ProgramsCache list event.
    event = events[75]

    self.CheckTimestamp(event.timestamp, '2009-08-04 15:22:18.419625')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.parser, 'explorer_programscache')
    self.assertEqual(
        event_data.data_type, 'windows:registry:explorer:programcache')

    expected_message = (
        'Key: {0:s} '
        'Value: ProgramsCache '
        'Entries: ['
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
        '19: Internet Explorer (No Add-ons).lnk]').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # The Windows Registry key event.
    event = events[76]

    self.CheckTimestamp(event.timestamp, '2009-08-04 15:22:18.419625')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.parser, 'explorer_programscache')
    self.assertEqual(event_data.data_type, 'windows:registry:key_value')

    expected_message = (
        '[{0:s}] '
        'Favorites: [REG_BINARY] (55 bytes) '
        'FavoritesChanges: [REG_DWORD_LE] 1 '
        'FavoritesResolve: [REG_BINARY] (8 bytes) '
        'StartMenu_Balloon_Time: [REG_BINARY] (8 bytes) '
        'StartMenu_Start_Time: [REG_BINARY] (8 bytes)').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 118)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2010-11-10 07:50:38.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(event_data.parser, 'explorer_programscache/shell_items')
    self.assertEqual(event_data.data_type, 'windows:shell_item:file_entry')


if __name__ == '__main__':
  unittest.main()
