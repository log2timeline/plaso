#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SkyDriveLog log parser."""

import unittest

from plaso.parsers import skydrivelog

from tests.parsers import test_lib


class SkyDriveLogUnitTest(test_lib.ParserTestCase):
  """Tests for the SkyDrive log parser."""

  def testParseErrorLog(self):
    """Tests the Parse function or error log."""
    parser = skydrivelog.SkyDriveLogParser()
    storage_writer = self._ParseFile(['skydriveerr.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 19)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'date_time': '2013-07-25 16:03:23.291',
        'data_type': 'skydrive:log:line',
        'detail': (
            'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
            '2013-07-25-180323.291 PID=0x8f4 TID=0x718 ContinuedFrom=')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'date_time': '2013-07-25 16:03:24.649',
        'data_type': 'skydrive:log:line',
        'detail': 'Sign in failed : DRX_E_AUTH_NO_VALID_CREDENTIALS,',
        'log_level': 'ERR',
        'module': 'AUTH',
        'source_code': 'authapi.cpp(280)'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-01 21:27:44.124',
        'data_type': 'skydrive:log:line',
        'detail': (
            'Received data from server,dwID=0x0;dwSize=0x3e;pbData=PNG 9 '
            'CON 48  <ping-response><wait>44</wait></ping-response>'),
        'log_level': 'VRB',
        'module': 'WNS',
        'source_code': 'absconn.cpp(177)'}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

  def testParseErrorLogUnicode(self):
    """Tests the Parse function on Unicode error log."""
    parser = skydrivelog.SkyDriveLogParser()
    storage_writer = self._ParseFile(['skydriveerr-unicode.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 19)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'date_time': '2013-07-25 16:04:02.669',
        'data_type': 'skydrive:log:line',
        'detail': (
            'No node found named Passport-Jméno-člena, no user name '
            'available,')}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

  def testParseLog(self):
    """Tests the Parse function on normal log."""
    parser = skydrivelog.SkyDriveLogParser()
    storage_writer = self._ParseFile(['skydrive.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 17)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'date_time': '2013-08-12 01:08:52.985',
        'data_type': 'skydrive:log:line'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-12 01:10:08.835',
        'data_type': 'skydrive:log:line'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-12 02:52:32.976',
        'data_type': 'skydrive:log:line',
        'detail': (
            'Received data from server,dwID=0x0;dwSize=0x15a;pbData=GET 5 '
            'WNS 331 Context: 2891  <channel-response><id>1;'
            '13714367258539257282</id><exp>2013-09-11T02:52:37Z</exp><url>'
            'https://bn1.notify.windows.com/?token=AgYAAAAdkHjSxiNH1mbF0Rp'
            '5TIv0Kz317BKYIAfBNO6szULCOEE2393owBINnPC5xoika5SJlNtXZ%2bwzaR'
            'VsPRcP1p64XFn90vGwr07DGZxfna%2bxBpBBplzZhLV9y%2fNV%2bBPxNmTI5'
            'sRgaZ%2foGvYCIj6MdeU1</url></channel-response>'),
        'log_level': 'VRB',
        'module': 'WNS',
        'source_code': 'absconn.cpp(177)'}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-12 03:18:57.232',
        'data_type': 'skydrive:log:line',
        'detail': (
            'Logging started. Version= 17.0.2011.0627 StartLocalTime: '
            '2013-08-11-231857.232 PID=0x1ef0 TID=0x1ef4 ContinuedFrom=')}

    self.CheckEventValues(storage_writer, events[13], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-31 03:45:37.940',
        'data_type': 'skydrive:log:line',
        'detail': (
            ',output=GET <- /MyData/LiveFolders?Filter=changes&InlineBlobs='
            'false&MaxItemCount=50&SyncToken=LM%3d63511875645970%3bID%3d7F0'
            '95149027848ED!103%3bLR%3d63513517536493%3bEP%3d2%3bTD%3dTrue&'
            'View=SkyDriveSync;m_httpStatus=0x130;hr=8004db30;m_pSink=null;'
            'cb=0x0;msec=0x4e'),
        'log_level': 'VRB',
        'module': 'PAL',
        'source_code': 'cwinhttp.cpp(1581)'}

    self.CheckEventValues(storage_writer, events[15], expected_event_values)


class SkyDriveOldLogUnitTest(test_lib.ParserTestCase):
  """Tests for the SkyDrive old log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = skydrivelog.SkyDriveOldLogParser()
    storage_writer = self._ParseFile(['skydrive_old.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 18)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'date_time': '2013-08-01 21:22:28.999',
        'data_type': 'skydrive:log:old:line',
        'log_level': 'DETAIL',
        'source_code': 'global.cpp:626!logVersionInfo',
        'text': '17.0.2011.0627 (Ship)'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-01 21:22:29.702',
        'data_type': 'skydrive:log:old:line'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-01 21:22:29.702',
        'data_type': 'skydrive:log:old:line'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-01 21:22:29.702',
        'data_type': 'skydrive:log:old:line',
        'text': (
            'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
            '103%3bLR%3d12345678905623%3aEP%3d2')}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-01 21:22:58.344',
        'data_type': 'skydrive:log:old:line'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-01 21:22:58.344',
        'data_type': 'skydrive:log:old:line'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'date_time': '2013-08-01 21:28:46.742',
        'data_type': 'skydrive:log:old:line',
        'text': 'SyncToken = Not a sync token (\xe0\xe8\xec\xf2\xf9)!'}

    self.CheckEventValues(storage_writer, events[17], expected_event_values)


if __name__ == '__main__':
  unittest.main()
