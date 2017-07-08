#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Shortcut (LNK) parser."""

import unittest

from plaso.formatters import winlnk  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import winlnk

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class WinLnkParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Shortcut (LNK) parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'example.lnk'])
  def testParse(self):
    """Tests the Parse function."""
    parser = winlnk.WinLnkParser()
    storage_writer = self._ParseFile([u'example.lnk'], parser)

    # Link information:
    # 	Creation time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Modification time		: Jul 14, 2009 01:39:18.220000000 UTC
    # 	Access time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Description			: @%windir%\system32\migwiz\wet.dll,-590
    # 	Relative path			: .\migwiz\migwiz.exe
    # 	Working directory		: %windir%\system32\migwiz
    # 	Icon location			: %windir%\system32\migwiz\migwiz.exe
    # 	Environment variables location	: %windir%\system32\migwiz\migwiz.exe

    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # A shortcut event.
    event = events[0]

    expected_string = u'@%windir%\\system32\\migwiz\\wet.dll,-590'
    self.assertEqual(event.description, expected_string)

    expected_string = u'.\\migwiz\\migwiz.exe'
    self.assertEqual(event.relative_path, expected_string)

    expected_string = u'%windir%\\system32\\migwiz'
    self.assertEqual(event.working_directory, expected_string)

    expected_string = u'%windir%\\system32\\migwiz\\migwiz.exe'
    self.assertEqual(event.icon_location, expected_string)
    self.assertEqual(event.env_var_location, expected_string)

    # The last accessed timestamp.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:29:02.849131')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)
    self.assertEqual(event.timestamp, expected_timestamp)

    # The creation timestamp.
    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-13 23:29:02.849131')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    # The last modification timestamp.
    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 01:39:18.220000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[@%windir%\\system32\\migwiz\\wet.dll,-590] '
        u'File size: 544768 '
        u'File attribute flags: 0x00000020 '
        u'env location: %windir%\\system32\\migwiz\\migwiz.exe '
        u'Relative path: .\\migwiz\\migwiz.exe '
        u'Working dir: %windir%\\system32\\migwiz '
        u'Icon location: %windir%\\system32\\migwiz\\migwiz.exe')

    expected_short_message = (
        u'[@%windir%\\system32\\migwiz\\wet.dll,-590]')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # A distributed link tracking event.
    event = events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 05:45:20.500012')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_uuid = u'846ee3bb-7039-11de-9d20-001d09fa5a1c'
    self.assertEqual(event.uuid, expected_uuid)
    self.assertEqual(event.mac_address, u'00:1d:09:fa:5a:1c')

  @shared_test_lib.skipUnlessHasTestFile([u'NeroInfoTool.lnk'])
  def testParseLinkTargetIdentifier(self):
    """Tests the Parse function on an LNK with a link target identifier."""
    parser = winlnk.WinLnkParser()
    storage_writer = self._ParseFile([u'NeroInfoTool.lnk'], parser)

    self.assertEqual(storage_writer.number_of_events, 20)

    events = list(storage_writer.GetEvents())

    # A shortcut event.
    event = events[16]

    expected_message = (
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

    expected_short_message = (
        u'[Nero InfoTool provides you with information about the most '
        u'important feature...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # A shell item event.
    event = events[12]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-06-05 20:13:20')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'Name: InfoTool.exe '
        u'Long name: InfoTool.exe '
        u'NTFS file reference: 81349-1 '
        u'Shell item path: <My Computer> C:\\Program Files (x86)\\Nero\\'
        u'Nero 9\\Nero InfoTool\\InfoTool.exe '
        u'Origin: NeroInfoTool.lnk')

    expected_short_message = (
        u'Name: InfoTool.exe '
        u'NTFS file reference: 81349-1 '
        u'Origin: NeroInfoTool.lnk')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
