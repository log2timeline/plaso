#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Explorer ProgramsCache Windows Registry plugin."""

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import programscache

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class ExplorerProgramCachePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Explorer ProgramsCache Windows Registry plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'NTUSER.DAT'])
  def testProcessStartPage(self):
    """Tests the Process function on a StartPage key."""
    test_file_entry = self._GetTestFileEntry([u'NTUSER.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\StartPage')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = programscache.ExplorerProgramsCachePlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_events, 77)

    events = list(storage_writer.GetEvents())

    # The ProgramsCache entry shell item event.
    event = events[0]

    expected_parser = u'explorer_programscache/shell_items'
    self.assertEqual(event.parser, expected_parser)

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:12:24')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_data_type = u'windows:shell_item:file_entry'
    self.assertEqual(event.data_type, expected_data_type)

    expected_message = (
        u'Name: Programs '
        u'Long name: Programs '
        u'Localized name: @shell32.dll,-21782 '
        u'Shell item path: Programs '
        u'Origin: {0:s} ProgramsCache').format(key_path)
    expected_short_message = (
        u'Name: Programs '
        u'Origin: HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\'
        u'CurrentVe...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # The ProgramsCache list event.
    event = events[75]

    expected_parser = u'explorer_programscache'
    self.assertEqual(event.parser, expected_parser)

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:22:18.419625')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_data_type = u'windows:registry:list'
    self.assertEqual(event.data_type, expected_data_type)

    expected_message = (
        u'Key: {0:s} '
        u'Value: ProgramsCache '
        u'List: ProgramsCache ['
        u'0: Programs '
        u'1: Internet Explorer.lnk '
        u'2: Outlook Express.lnk '
        u'3: Remote Assistance.lnk '
        u'4: Windows Media Player.lnk '
        u'5: Programs Accessories '
        u'6: Address Book.lnk '
        u'7: Command Prompt.lnk '
        u'8: Notepad.lnk '
        u'9: Program Compatibility Wizard.lnk '
        u'10: Synchronize.lnk '
        u'11: Tour Windows XP.lnk '
        u'12: Windows Explorer.lnk '
        u'13: Programs Accessories\\Accessibility '
        u'14: Magnifier.lnk '
        u'15: Narrator.lnk '
        u'16: On-Screen Keyboard.lnk '
        u'17: Utility Manager.lnk '
        u'18: Programs Accessories\\System Tools '
        u'19: Internet Explorer (No Add-ons).lnk]').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # The Windows Registry key event.
    event = events[76]

    expected_parser = u'explorer_programscache'
    self.assertEqual(event.parser, expected_parser)

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:22:18.419625')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_data_type = u'windows:registry:key_value'
    self.assertEqual(event.data_type, expected_data_type)

  @shared_test_lib.skipUnlessHasTestFile([u'NTUSER-WIN7.DAT'])
  def testProcessStartPage2(self):
    """Tests the Process function on a StartPage2 key."""
    test_file_entry = self._GetTestFileEntry([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\StartPage2')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = programscache.ExplorerProgramsCachePlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_events, 118)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_parser = u'explorer_programscache/shell_items'
    self.assertEqual(event.parser, expected_parser)

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:50:38')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_data_type = u'windows:shell_item:file_entry'
    self.assertEqual(event.data_type, expected_data_type)


if __name__ == '__main__':
  unittest.main()
