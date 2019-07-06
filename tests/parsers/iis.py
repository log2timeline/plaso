#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows IIS log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import iis as _  # pylint: disable=unused-import
from plaso.parsers import iis

from tests.parsers import test_lib


class WinIISUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows IIS parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = iis.WinIISParser()
    storage_writer = self._ParseFile(['iis.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 12)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-07-30 00:00:00.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.source_ip, '10.10.10.100')
    self.assertEqual(event_data.dest_ip, '10.10.10.100')
    self.assertEqual(event_data.dest_port, 80)

    expected_message = (
        'GET /some/image/path/something.jpg '
        '[ 10.10.10.100 > 10.10.10.100 : 80 ] '
        'HTTP Status: 200 '
        'User Agent: Mozilla/4.0+(compatible;+Win32;'
        '+WinHttp.WinHttpRequest.5)')
    expected_short_message = (
        'GET /some/image/path/something.jpg '
        '[ 10.10.10.100 > 10.10.10.100 : 80 ]')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[5]

    self.CheckTimestamp(event.timestamp, '2013-07-30 00:00:05.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.http_method, 'GET')
    self.assertEqual(event_data.http_status, 200)
    self.assertEqual(
        event_data.requested_uri_stem, '/some/image/path/something.jpg')

    event = events[1]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'GET /some/image/path/something.htm '
        '[ 22.22.22.200 > 10.10.10.100 : 80 ] '
        'HTTP Status: 404 '
        'User Agent: Mozilla/5.0+(Macintosh;+Intel+Mac+OS+X+10_6_8)'
        '+AppleWebKit/534.57.2+(KHTML,+like+Gecko)+Version/5.1.7'
        '+Safari/534.57.2')
    expected_short_message = (
        'GET /some/image/path/something.htm '
        '[ 22.22.22.200 > 10.10.10.100 : 80 ]')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[11]
    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_query_string = 'ID=ERROR[`cat%20passwd|echo`]'
    self.assertEqual(expected_query_string, event_data.cs_uri_query)

  def testParseWithoutDate(self):
    """Tests the Parse function with logs without a date column."""
    parser = iis.WinIISParser()
    storage_writer = self._ParseFile(['iis_without_date.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 11)

    events = list(storage_writer.GetEvents())

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-07-30 00:00:03.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.protocol_version, 'HTTP/1.1')


if __name__ == '__main__':
  unittest.main()
