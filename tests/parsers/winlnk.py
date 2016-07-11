#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Shortcut (LNK) parser."""

import unittest

from plaso.formatters import winlnk as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winlnk

from tests.parsers import test_lib


class WinLnkParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Shortcut (LNK) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser_object = winlnk.WinLnkParser()
    storage_writer = self._ParseFile(
        [u'example.lnk'], parser_object)

    # Link information:
    # 	Creation time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Modification time		: Jul 14, 2009 01:39:18.220000000 UTC
    # 	Access time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Description			: @%windir%\system32\migwiz\wet.dll,-590
    # 	Relative path			: .\migwiz\migwiz.exe
    # 	Working directory		: %windir%\system32\migwiz
    # 	Icon location			: %windir%\system32\migwiz\migwiz.exe
    # 	Environment variables location	: %windir%\system32\migwiz\migwiz.exe

    self.assertEqual(len(storage_writer.events), 5)

    # A shortcut event object.
    event_object = storage_writer.events[0]

    expected_string = u'@%windir%\\system32\\migwiz\\wet.dll,-590'
    self.assertEqual(event_object.description, expected_string)

    expected_string = u'.\\migwiz\\migwiz.exe'
    self.assertEqual(event_object.relative_path, expected_string)

    expected_string = u'%windir%\\system32\\migwiz'
    self.assertEqual(event_object.working_directory, expected_string)

    expected_string = u'%windir%\\system32\\migwiz\\migwiz.exe'
    self.assertEqual(event_object.icon_location, expected_string)
    self.assertEqual(event_object.env_var_location, expected_string)

    # The last accessed timestamp.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:29:02.849131')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The creation timestamp.
    event_object = storage_writer.events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:29:02.849131')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The last modification timestamp.
    event_object = storage_writer.events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 01:39:18.220000')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[@%windir%\\system32\\migwiz\\wet.dll,-590] '
        u'File size: 544768 '
        u'File attribute flags: 0x00000020 '
        u'env location: %windir%\\system32\\migwiz\\migwiz.exe '
        u'Relative path: .\\migwiz\\migwiz.exe '
        u'Working dir: %windir%\\system32\\migwiz '
        u'Icon location: %windir%\\system32\\migwiz\\migwiz.exe')

    expected_msg_short = (
        u'[@%windir%\\system32\\migwiz\\wet.dll,-590]')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # A distributed link tracking event object.
    event_object = storage_writer.events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 05:45:20.500012')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_uuid = u'846ee3bb-7039-11de-9d20-001d09fa5a1c'
    self.assertEqual(event_object.uuid, expected_uuid)
    self.assertEqual(event_object.mac_address, u'00:1d:09:fa:5a:1c')

  def testParseLinkTargetIdentifier(self):
    """Tests the Parse function on an LNK with a link target identifier."""
    parser_object = winlnk.WinLnkParser()
    storage_writer = self._ParseFile(
        [u'NeroInfoTool.lnk'], parser_object)

    self.assertEqual(len(storage_writer.events), 20)

    # A shortcut event object.
    event_object = storage_writer.events[16]

    expected_msg = (
        u'[Nero InfoTool provides you with information about the most '
        u'important features of installed drives, inserted discs, installed '
        u'software and much more. With Nero InfoTool you can find out all '
        u'about your drive and your system configuration.] '
        u'File size: 4635160 '
        u'File attribute flags: 0x00000020 '
        u'Drive type: 3 '
        u'Drive serial number: 0x70ecfa33 '
        u'Volume label: OS '
        u'Local path: C:\\Program Files (x86)\\Nero\\Nero 9\\Nero InfoTool\\'
        u'InfoTool.exe '
        u'cmd arguments: -ScParameter=30002   '
        u'Relative path: ..\\..\\..\\..\\..\\..\\..\\..\\Program Files (x86)\\'
        u'Nero\\Nero 9\\Nero InfoTool\\InfoTool.exe '
        u'Working dir: C:\\Program Files (x86)\\Nero\\Nero 9\\Nero InfoTool '
        u'Icon location: %ProgramFiles%\\Nero\\Nero 9\\Nero InfoTool\\'
        u'InfoTool.exe '
        u'Link target: <My Computer> C:\\Program Files (x86)\\Nero\\Nero 9\\'
        u'Nero InfoTool\\InfoTool.exe')

    expected_msg_short = (
        u'[Nero InfoTool provides you with information about the most '
        u'important feature...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # A shell item event object.
    event_object = storage_writer.events[12]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-06-05 20:13:20')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'Name: InfoTool.exe '
        u'Long name: InfoTool.exe '
        u'NTFS file reference: 81349-1 '
        u'Shell item path: <My Computer> C:\\Program Files (x86)\\Nero\\'
        u'Nero 9\\Nero InfoTool\\InfoTool.exe '
        u'Origin: NeroInfoTool.lnk')

    expected_msg_short = (
        u'Name: InfoTool.exe '
        u'NTFS file reference: 81349-1 '
        u'Origin: NeroInfoTool.lnk')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
