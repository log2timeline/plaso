#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Explorer ProgramsCache Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import programscache

from tests.parsers.winreg_plugins import test_lib


class ExplorerProgramCachePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Explorer ProgramsCache Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = programscache.ExplorerProgramsCachePlugin()

  def testProcessStartPage(self):
    """Tests the Process function on a StartPage key."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\StartPage')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 77)

    # The ProgramsCache entry shell item event.
    event_object = event_objects[0]

    expected_parser = u'explorer_programscache/shell_items'
    self.assertEqual(event_object.parser, expected_parser)

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:12:24')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_data_type = 'windows:shell_item:file_entry'
    self.assertEqual(event_object.data_type, expected_data_type)

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

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    # The ProgramsCache list event.
    event_object = event_objects[75]

    expected_parser = u'explorer_programscache'
    self.assertEqual(event_object.parser, expected_parser)

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.WRITTEN_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:22:18.419625')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_data_type = 'windows:registry:list'
    self.assertEqual(event_object.data_type, expected_data_type)

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
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    # The Windows Registry key event.
    event_object = event_objects[76]

    expected_parser = u'explorer_programscache'
    self.assertEqual(event_object.parser, expected_parser)

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.WRITTEN_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:22:18.419625')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_data_type = 'windows:registry:key_value'
    self.assertEqual(event_object.data_type, expected_data_type)

  def testProcessStartPage2(self):
    """Tests the Process function on a StartPage2 key."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\StartPage2')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 118)

    event_object = event_objects[0]

    expected_parser = u'explorer_programscache/shell_items'
    self.assertEqual(event_object.parser, expected_parser)

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:50:38')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_data_type = 'windows:shell_item:file_entry'
    self.assertEqual(event_object.data_type, expected_data_type)


if __name__ == '__main__':
  unittest.main()
