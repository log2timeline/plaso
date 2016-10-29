#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Symantec AV Log parser."""

import unittest

from plaso.formatters import symantec  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import symantec

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib

import pytz  # pylint: disable=wrong-import-order


class SymantecAccessProtectionUnitTest(test_lib.ParserTestCase):
  """Tests for the Symantec AV Log parser."""

  def testConvertToTimestamp(self):
    """Tests the _ConvertToTimestamp function."""
    parser_object = symantec.SymantecParser()

    # pylint: disable=protected-access
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2002-11-19 08:01:34')
    timestamp = parser_object._ConvertToTimestamp(
        u'200A13080122', timezone=pytz.UTC)
    self.assertEqual(timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-11-30 10:47:29')
    timestamp = parser_object._ConvertToTimestamp(
        u'2A0A1E0A2F1D', timezone=pytz.UTC)
    self.assertEqual(timestamp, expected_timestamp)

  @shared_test_lib.skipUnlessHasTestFile([u'Symantec.Log'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = symantec.SymantecParser()
    storage_writer = self._ParseFile([u'Symantec.Log'], parser_object)

    # The file contains 8 lines which should result in 8 event objects.
    self.assertEqual(len(storage_writer.events), 8)

    # Test the second entry:
    event_object = storage_writer.events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-11-30 10:47:29')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.user, u'davnads')
    expected_file = (
        u'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt')
    self.assertEqual(event_object.file, expected_file)

    expected_msg = (
        u'Event Name: GL_EVENT_INFECTION; '
        u'Category Name: GL_CAT_INFECTION; '
        u'Malware Name: W32.Changeup!gen33; '
        u'Malware Path: '
        u'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt; '
        u'Action0: Unknown; '
        u'Action1: Clean virus from file; '
        u'Action2: Delete infected file; '
        u'Scan ID: 0; '
        u'Event Data: 201\t4\t6\t1\t65542\t0\t0\t0\t0\t0\t0')
    expected_msg_short = (
        u'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt; '
        u'W32.Changeup!gen33; '
        u'Unknown; ...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
