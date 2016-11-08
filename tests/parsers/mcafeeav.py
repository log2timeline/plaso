#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the McAfee AV Log parser."""

import unittest

from plaso.formatters import mcafeeav  # pylint: disable=unused-import
from plaso.parsers import mcafeeav

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class McafeeAccessProtectionUnitTest(test_lib.ParserTestCase):
  """Tests for the McAfee AV Log parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'AccessProtectionLog.txt'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = mcafeeav.McafeeAccessProtectionParser()
    storage_writer = self._ParseFile(
        [u'AccessProtectionLog.txt'], parser_object)

    # The file contains 14 lines which results in 14 event objects.
    self.assertEqual(len(storage_writer.events), 14)

    # Test that the UTF-8 byte order mark gets removed from the first line.
    event_object = storage_writer.events[0]

    self.assertEqual(event_object.timestamp, 1380292946000000)

    # Test this entry:
    # 9/27/2013 2:42:26 PM  Blocked by Access Protection rule
    #   SOMEDOMAIN\someUser C:\Windows\System32\procexp64.exe C:\Program Files
    # (x86)\McAfee\Common Framework\UdaterUI.exe  Common Standard
    # Protection:Prevent termination of McAfee processes  Action blocked :
    # Terminate

    event_object = storage_writer.events[1]

    self.assertEqual(event_object.timestamp, 1380292959000000)
    self.assertEqual(event_object.username, u'SOMEDOMAIN\\someUser')
    self.assertEqual(
        event_object.full_path, u'C:\\Windows\\System32\\procexp64.exe')

    expected_msg = (
        u'File Name: C:\\Windows\\System32\\procexp64.exe '
        u'User: SOMEDOMAIN\\someUser '
        u'C:\\Program Files (x86)\\McAfee\\Common Framework\\Frame'
        u'workService.exe '
        u'Blocked by Access Protection rule  '
        u'Common Standard Protection:Prevent termination of McAfee processes '
        u'Action blocked : Terminate')
    expected_msg_short = (
        u'C:\\Windows\\System32\\procexp64.exe '
        u'Action blocked : Terminate')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
