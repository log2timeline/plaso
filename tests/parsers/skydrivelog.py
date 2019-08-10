#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SkyDriveLog log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import skydrivelog as _  # pylint: disable=unused-import
from plaso.parsers import skydrivelog

from tests.parsers import test_lib


class SkyDriveLogUnitTest(test_lib.ParserTestCase):
  """Tests for the SkyDrive log parser."""

  def testParseErrorLog(self):
    """Tests the Parse function or error log."""
    parser = skydrivelog.SkyDriveLogParser()
    storage_writer = self._ParseFile(['skydriveerr.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 19)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-07-25 16:03:23.291000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        '2013-07-25-180323.291 PID=0x8f4 TID=0x718 ContinuedFrom=')
    expected_short_message = (
        'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        '2013-07-25-180323.29...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-07-25 16:03:24.649000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[AUTH authapi.cpp(280) ERR] Sign in failed : '
        'DRX_E_AUTH_NO_VALID_CREDENTIALS,')
    expected_short_message = (
        'Sign in failed : DRX_E_AUTH_NO_VALID_CREDENTIALS,')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[18]

    self.CheckTimestamp(event.timestamp, '2013-08-01 21:27:44.124000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[WNS absconn.cpp(177) VRB] Received data from server,'
        'dwID=0x0;dwSize=0x3e;pbData=PNG 9 CON 48  <ping-response>'
        '<wait>44</wait></ping-response>')
    expected_short_message = (
        'Received data from server,dwID=0x0;dwSize=0x3e;pbData=PNG 9 CON 48  '
        '<ping-res...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseErrorLogUnicode(self):
    """Tests the Parse function on Unicode error log."""
    parser = skydrivelog.SkyDriveLogParser()
    storage_writer = self._ParseFile(['skydriveerr-unicode.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 19)

    events = list(storage_writer.GetEvents())

    # TODO: check if this test passes because the encoding on my system
    # is UTF-8.
    event = events[3]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_detail = (
        'No node found named Passport-Jméno-člena, no user name available,')
    self.assertEqual(event_data.detail, expected_detail)

  def testParseLog(self):
    """Tests the Parse function on normal log."""
    parser = skydrivelog.SkyDriveLogParser()
    storage_writer = self._ParseFile(['skydrive.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 17)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-08-12 01:08:52.985000')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-08-12 01:10:08.835000')

    event = events[11]

    self.CheckTimestamp(event.timestamp, '2013-08-12 02:52:32.976000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[WNS absconn.cpp(177) VRB] Received data from server,dwID=0x0;'
        'dwSize=0x15a;pbData=GET 5 WNS 331 Context: 2891  <channel-response>'
        '<id>1;13714367258539257282</id><exp>2013-09-11T02:52:37Z</exp><url>'
        'https://bn1.notify.windows.com/?token=AgYAAAAdkHjSxiNH1mbF0Rp5TIv0K'
        'z317BKYIAfBNO6szULCOEE2393owBINnPC5xoika5SJlNtXZ%2bwzaRVsPRcP1p64XF'
        'n90vGwr07DGZxfna%2bxBpBBplzZhLV9y%2fNV%2bBPxNmTI5sRgaZ%2foGvYCIj6Md'
        'eU1</url></channel-response>')
    expected_short_message = (
        'Received data from server,dwID=0x0;dwSize=0x15a;pbData=GET 5 WNS '
        '331 Context:...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[13]

    self.CheckTimestamp(event.timestamp, '2013-08-12 03:18:57.232000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        '2013-08-11-231857.232 PID=0x1ef0 TID=0x1ef4 ContinuedFrom=')
    expected_short_message = (
        'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
        '2013-08-11-231857.23...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[15]

    self.CheckTimestamp(event.timestamp, '2013-08-31 03:45:37.940000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[PAL cwinhttp.cpp(1581) VRB] ,output=GET <- /MyData/LiveFolders?'
        'Filter=changes&InlineBlobs=false&MaxItemCount=50&SyncToken=LM%3d6351'
        '1875645970%3bID%3d7F095149027848ED!103%3bLR%3d63513517536493%3bEP%3d'
        '2%3bTD%3dTrue&View=SkyDriveSync;m_httpStatus=0x130;hr=8004db30;'
        'm_pSink=null;cb=0x0;msec=0x4e')
    expected_short_message = (
        ',output=GET <- /MyData/LiveFolders?Filter=changes&InlineBlobs='
        'false&MaxItemCo...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


class SkyDriveOldLogUnitTest(test_lib.ParserTestCase):
  """Tests for the SkyDrive old log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = skydrivelog.SkyDriveOldLogParser()
    storage_writer = self._ParseFile(['skydrive_old.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 18)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-08-01 21:22:28.999000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[global.cpp:626!logVersionInfo] (DETAIL) 17.0.2011.0627 (Ship)')
    expected_short_message = (
        '17.0.2011.0627 (Ship)')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-08-01 21:22:29.702000')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-08-01 21:22:29.702000')

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2013-08-01 21:22:29.702000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
        '103%3bLR%3d12345678905623%3aEP%3d2')
    expected_short_message = (
        'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
        '103%3bLR%3d1234567890...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[4]

    self.CheckTimestamp(event.timestamp, '2013-08-01 21:22:58.344000')

    event = events[5]

    self.CheckTimestamp(event.timestamp, '2013-08-01 21:22:58.344000')

    event = events[17]

    self.CheckTimestamp(event.timestamp, '2013-08-01 21:28:46.742000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'SyncToken = Not a sync token (\xe0\xe8\xec\xf2\xf9)!')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
