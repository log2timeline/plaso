#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SkyDriveLog log parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import skydrivelog as skydrivelog_formatter
from plaso.lib import timelib
from plaso.parsers import skydrivelog

from tests.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogUnitTest(test_lib.ParserTestCase):
  """Tests for the SkyDrive log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = skydrivelog.SkyDriveLogParser()

  def testParseErrorLog(self):
    """Tests the Parse function or error log."""
    test_file = self._GetTestFilePath([u'skydriveerr.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 19)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-25 16:03:23.291')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-25 16:03:24.649')
    self.assertEqual(event_objects[1].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:27:44.124')
    self.assertEqual(event_objects[18].timestamp, expected_timestamp)

    expected_string = (
        'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        '2013-07-25-180323.291 PID=0x8f4 TID=0x718 ContinuedFrom=')
    expected_string_short = (
        u'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        '2013-07-25-180323.29...')
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_string_short)

    expected_string = (
        u'[AUTH authapi.cpp(280) ERR] Sign in failed : '
        u'DRX_E_AUTH_NO_VALID_CREDENTIALS,')
    expected_string_short = (
        u'Sign in failed : DRX_E_AUTH_NO_VALID_CREDENTIALS,')
    self._TestGetMessageStrings(
        event_objects[1], expected_string, expected_string_short)

    expected_string = (
        u'[WNS absconn.cpp(177) VRB] Received data from server,'
        u'dwID=0x0;dwSize=0x3e;pbData=PNG 9 CON 48  <ping-response>'
        u'<wait>44</wait></ping-response>')
    expected_string_short = (
        u'Received data from server,dwID=0x0;dwSize=0x3e;pbData=PNG 9 CON 48  '
        '<ping-res...')
    self._TestGetMessageStrings(
        event_objects[18], expected_string, expected_string_short)

  def testParseErrorLogUnicode(self):
    """Tests the Parse function on Unicode error log."""
    test_file = self._GetTestFilePath([u'skydriveerr-unicode.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 19)

    # TODO: check if this test passes because the encoding on my system
    # is UTF-8.
    expected_detail = (
        u'No node found named Passport-Jméno-člena, no user name available,')
    self.assertEqual(event_objects[3].detail, expected_detail)

  def testParseLog(self):
    """Tests the Parse function on normal log."""
    test_file = self._GetTestFilePath([u'skydrive.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 17)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-12 01:08:52.985')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-12 01:10:08.835')
    self.assertEqual(event_objects[1].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-12 02:52:32.976')
    self.assertEqual(event_objects[11].timestamp, expected_timestamp)

    expected_string = (
        u'[WNS absconn.cpp(177) VRB] Received data from server,dwID=0x0;'
        'dwSize=0x15a;pbData=GET 5 WNS 331 Context: 2891  <channel-response>'
        '<id>1;13714367258539257282</id><exp>2013-09-11T02:52:37Z</exp><url>'
        'https://bn1.notify.windows.com/?token=AgYAAAAdkHjSxiNH1mbF0Rp5TIv0K'
        'z317BKYIAfBNO6szULCOEE2393owBINnPC5xoika5SJlNtXZ%2bwzaRVsPRcP1p64XF'
        'n90vGwr07DGZxfna%2bxBpBBplzZhLV9y%2fNV%2bBPxNmTI5sRgaZ%2foGvYCIj6Md'
        'eU1</url></channel-response>')
    expected_string_short = (
        u'Received data from server,dwID=0x0;dwSize=0x15a;pbData=GET 5 WNS '
        '331 Context:...')
    self._TestGetMessageStrings(
        event_objects[11], expected_string, expected_string_short)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-12 03:18:57.232')
    self.assertEqual(event_objects[13].timestamp, expected_timestamp)

    expected_string = (
        u'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        '2013-08-11-231857.232 PID=0x1ef0 TID=0x1ef4 ContinuedFrom=')
    expected_string_short = (
        u'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        '2013-08-11-231857.23...')
    self._TestGetMessageStrings(
        event_objects[13], expected_string, expected_string_short)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-31 03:45:37.940')
    self.assertEqual(event_objects[15].timestamp, expected_timestamp)

    expected_string = (
        u'[PAL cwinhttp.cpp(1581) VRB] ,output=GET <- /MyData/LiveFolders?'
        'Filter=changes&InlineBlobs=false&MaxItemCount=50&SyncToken=LM%3d6351'
        '1875645970%3bID%3d7F095149027848ED!103%3bLR%3d63513517536493%3bEP%3d'
        '2%3bTD%3dTrue&View=SkyDriveSync;m_httpStatus=0x130;hr=8004db30;'
        'm_pSink=null;cb=0x0;msec=0x4e')
    expected_string_short = (
        u',output=GET <- /MyData/LiveFolders?Filter=changes&InlineBlobs='
        'false&MaxItemCo...')
    self._TestGetMessageStrings(
        event_objects[15], expected_string, expected_string_short)


class SkyDriveOldLogUnitTest(test_lib.ParserTestCase):
  """Tests for the SkyDrive old log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = skydrivelog.SkyDriveOldLogParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'skydrive_old.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 18)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:22:28.999')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:22:29.702')
    self.assertEqual(event_objects[1].timestamp, expected_timestamp)
    self.assertEqual(event_objects[2].timestamp, expected_timestamp)
    self.assertEqual(event_objects[3].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:22:58.344')
    self.assertEqual(event_objects[4].timestamp, expected_timestamp)
    self.assertEqual(event_objects[5].timestamp, expected_timestamp)

    expected_msg = (
        u'[global.cpp:626!logVersionInfo] (DETAIL) 17.0.2011.0627 (Ship)')
    expected_msg_short = (
        u'17.0.2011.0627 (Ship)')
    self._TestGetMessageStrings(
        event_objects[0], expected_msg, expected_msg_short)

    expected_msg = (
        u'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
        u'103%3bLR%3d12345678905623%3aEP%3d2')
    expected_msg_short = (
        u'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
        u'103%3bLR%3d1234567890...')
    self._TestGetMessageStrings(
        event_objects[3], expected_msg, expected_msg_short)

    expected_string = (
        u'SyncToken = Not a sync token (\xe0\xe8\xec\xf2\xf9)!')
    self._TestGetMessageStrings(
        event_objects[17], expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
