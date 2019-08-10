#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Shortcut (LNK) parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winlnk as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import winlnk

from tests.parsers import test_lib


class WinLnkParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Shortcut (LNK) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winlnk.WinLnkParser()
    storage_writer = self._ParseFile(['example.lnk'], parser)

    # Link information:
    # 	Creation time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Modification time		: Jul 14, 2009 01:39:18.220000000 UTC
    # 	Access time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Description			: @%windir%\system32\migwiz\wet.dll,-590
    # 	Relative path			: .\migwiz\migwiz.exe
    # 	Working directory		: %windir%\system32\migwiz
    # 	Icon location			: %windir%\system32\migwiz\migwiz.exe
    # 	Environment variables location	: %windir%\system32\migwiz\migwiz.exe

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # A shortcut event.
    event = events[0]

    # The last accessed timestamp.
    self.CheckTimestamp(event.timestamp, '2009-07-13 23:29:02.849131')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'windows:lnk:link')
    self.assertEqual(
        event_data.description, '@%windir%\\system32\\migwiz\\wet.dll,-590')
    self.assertEqual(event_data.relative_path, '.\\migwiz\\migwiz.exe')
    self.assertEqual(event_data.working_directory, '%windir%\\system32\\migwiz')
    self.assertEqual(
        event_data.icon_location, '%windir%\\system32\\migwiz\\migwiz.exe')
    self.assertEqual(
        event_data.env_var_location, '%windir%\\system32\\migwiz\\migwiz.exe')

    # The creation timestamp.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2009-07-13 23:29:02.849131')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    # The last modification timestamp.
    event = events[2]

    self.CheckTimestamp(event.timestamp, '2009-07-14 01:39:18.220000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'windows:lnk:link')

    expected_message = (
        '[@%windir%\\system32\\migwiz\\wet.dll,-590] '
        'File size: 544768 '
        'File attribute flags: 0x00000020 '
        'env location: %windir%\\system32\\migwiz\\migwiz.exe '
        'Relative path: .\\migwiz\\migwiz.exe '
        'Working dir: %windir%\\system32\\migwiz '
        'Icon location: %windir%\\system32\\migwiz\\migwiz.exe')

    expected_short_message = (
        '[@%windir%\\system32\\migwiz\\wet.dll,-590] '
        '%windir%\\system32\\migwiz\\.\\migwiz\\mi...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # A distributed link tracking event.
    event = events[4]

    self.CheckTimestamp(event.timestamp, '2009-07-14 05:45:20.500012')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_uuid = '846ee3bb-7039-11de-9d20-001d09fa5a1c'
    self.assertEqual(event_data.uuid, expected_uuid)
    self.assertEqual(event_data.mac_address, '00:1d:09:fa:5a:1c')

  def testParseLinkTargetIdentifier(self):
    """Tests the Parse function on an LNK with a link target identifier."""
    parser = winlnk.WinLnkParser()
    storage_writer = self._ParseFile(['NeroInfoTool.lnk'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 20)

    events = list(storage_writer.GetEvents())

    # A shortcut event.
    event = events[16]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[Nero InfoTool provides you with information about the most '
        'important features of installed drives, inserted discs, installed '
        'software and much more. With Nero InfoTool you can find out all '
        'about your drive and your system configuration.] '
        'File size: 4635160 '
        'File attribute flags: 0x00000020 '
        'Drive type: 3 '
        'Drive serial number: 0x70ecfa33 '
        'Volume label: OS '
        'Local path: C:\\Program Files (x86)\\Nero\\Nero 9\\Nero InfoTool\\'
        'InfoTool.exe '
        'cmd arguments: -ScParameter=30002   '
        'Relative path: ..\\..\\..\\..\\..\\..\\..\\..\\Program Files (x86)\\'
        'Nero\\Nero 9\\Nero InfoTool\\InfoTool.exe '
        'Working dir: C:\\Program Files (x86)\\Nero\\Nero 9\\Nero InfoTool '
        'Icon location: %ProgramFiles%\\Nero\\Nero 9\\Nero InfoTool\\'
        'InfoTool.exe '
        'Link target: <My Computer> C:\\Program Files (x86)\\Nero\\Nero 9\\'
        'Nero InfoTool\\InfoTool.exe')

    expected_short_message = (
        '[Nero InfoTool provides you with information about the most '
        'important feature...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # A shell item event.
    event = events[12]

    self.CheckTimestamp(event.timestamp, '2009-06-05 20:13:20.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Name: InfoTool.exe '
        'Long name: InfoTool.exe '
        'NTFS file reference: 81349-1 '
        'Shell item path: <My Computer> C:\\Program Files (x86)\\Nero\\'
        'Nero 9\\Nero InfoTool\\InfoTool.exe '
        'Origin: NeroInfoTool.lnk')

    expected_short_message = (
        'Name: InfoTool.exe '
        'NTFS file reference: 81349-1 '
        'Origin: NeroInfoTool.lnk')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
