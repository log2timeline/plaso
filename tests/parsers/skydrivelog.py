#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SkyDriveLog log parser."""

import unittest

from plaso.formatters import skydrivelog  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import skydrivelog

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogUnitTest(test_lib.ParserTestCase):
  """Tests for the SkyDrive log parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'skydriveerr.log'])
  def testParseErrorLog(self):
    """Tests the Parse function or error log."""
    parser = skydrivelog.SkyDriveLogParser()
    storage_writer = self._ParseFile([u'skydriveerr.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 19)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-25 16:03:23.291')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        u'2013-07-25-180323.291 PID=0x8f4 TID=0x718 ContinuedFrom=')
    expected_short_message = (
        u'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        u'2013-07-25-180323.29...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-25 16:03:24.649')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[AUTH authapi.cpp(280) ERR] Sign in failed : '
        u'DRX_E_AUTH_NO_VALID_CREDENTIALS,')
    expected_short_message = (
        u'Sign in failed : DRX_E_AUTH_NO_VALID_CREDENTIALS,')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[18]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:27:44.124')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[WNS absconn.cpp(177) VRB] Received data from server,'
        u'dwID=0x0;dwSize=0x3e;pbData=PNG 9 CON 48  <ping-response>'
        u'<wait>44</wait></ping-response>')
    expected_short_message = (
        u'Received data from server,dwID=0x0;dwSize=0x3e;pbData=PNG 9 CON 48  '
        u'<ping-res...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'skydriveerr-unicode.log'])
  def testParseErrorLogUnicode(self):
    """Tests the Parse function on Unicode error log."""
    parser = skydrivelog.SkyDriveLogParser()
    storage_writer = self._ParseFile(
        [u'skydriveerr-unicode.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 19)

    events = list(storage_writer.GetEvents())

    # TODO: check if this test passes because the encoding on my system
    # is UTF-8.
    event = events[3]

    expected_detail = (
        u'No node found named Passport-Jméno-člena, no user name available,')
    self.assertEqual(event.detail, expected_detail)

  @shared_test_lib.skipUnlessHasTestFile([u'skydrive.log'])
  def testParseLog(self):
    """Tests the Parse function on normal log."""
    parser = skydrivelog.SkyDriveLogParser()
    storage_writer = self._ParseFile([u'skydrive.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 17)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-12 01:08:52.985')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-12 01:10:08.835')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[11]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-12 02:52:32.976')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[WNS absconn.cpp(177) VRB] Received data from server,dwID=0x0;'
        u'dwSize=0x15a;pbData=GET 5 WNS 331 Context: 2891  <channel-response>'
        u'<id>1;13714367258539257282</id><exp>2013-09-11T02:52:37Z</exp><url>'
        u'https://bn1.notify.windows.com/?token=AgYAAAAdkHjSxiNH1mbF0Rp5TIv0K'
        u'z317BKYIAfBNO6szULCOEE2393owBINnPC5xoika5SJlNtXZ%2bwzaRVsPRcP1p64XF'
        u'n90vGwr07DGZxfna%2bxBpBBplzZhLV9y%2fNV%2bBPxNmTI5sRgaZ%2foGvYCIj6Md'
        u'eU1</url></channel-response>')
    expected_short_message = (
        u'Received data from server,dwID=0x0;dwSize=0x15a;pbData=GET 5 WNS '
        u'331 Context:...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[13]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-12 03:18:57.232')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        u'2013-08-11-231857.232 PID=0x1ef0 TID=0x1ef4 ContinuedFrom=')
    expected_short_message = (
        u'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        u'2013-08-11-231857.23...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[15]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-31 03:45:37.940')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[PAL cwinhttp.cpp(1581) VRB] ,output=GET <- /MyData/LiveFolders?'
        u'Filter=changes&InlineBlobs=false&MaxItemCount=50&SyncToken=LM%3d6351'
        u'1875645970%3bID%3d7F095149027848ED!103%3bLR%3d63513517536493%3bEP%3d'
        u'2%3bTD%3dTrue&View=SkyDriveSync;m_httpStatus=0x130;hr=8004db30;'
        u'm_pSink=null;cb=0x0;msec=0x4e')
    expected_short_message = (
        u',output=GET <- /MyData/LiveFolders?Filter=changes&InlineBlobs='
        u'false&MaxItemCo...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


class SkyDriveOldLogUnitTest(test_lib.ParserTestCase):
  """Tests for the SkyDrive old log parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'skydrive_old.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = skydrivelog.SkyDriveOldLogParser()
    storage_writer = self._ParseFile([u'skydrive_old.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 18)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:22:28.999')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[global.cpp:626!logVersionInfo] (DETAIL) 17.0.2011.0627 (Ship)')
    expected_short_message = (
        u'17.0.2011.0627 (Ship)')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:22:29.702')

    event = events[1]
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[2]
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[3]
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
        u'103%3bLR%3d12345678905623%3aEP%3d2')
    expected_short_message = (
        u'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
        u'103%3bLR%3d1234567890...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:22:58.344')

    event = events[4]
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[5]
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[17]
    expected_message = (
        u'SyncToken = Not a sync token (\xe0\xe8\xec\xf2\xf9)!')
    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
