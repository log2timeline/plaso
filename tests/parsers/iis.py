#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows IIS log parser."""

import unittest

from plaso.formatters import iis  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import iis

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


__author__ = 'Ashley Holtz (ashley.a.holtz@gmail.com)'


class WinIISUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows IIS parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'iis.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = iis.WinIISParser()
    storage_writer = self._ParseFile([u'iis.log'], parser_object)

    self.assertEqual(len(storage_writer.events), 11)

    event_object = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-30 00:00:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.source_ip, u'10.10.10.100')
    self.assertEqual(event_object.dest_ip, u'10.10.10.100')
    self.assertEqual(event_object.dest_port, 80)

    expected_msg = (
        u'GET /some/image/path/something.jpg '
        u'[ 10.10.10.100 > 10.10.10.100 : 80 ] '
        u'HTTP Status: 200 '
        u'User Agent: Mozilla/4.0+(compatible;+Win32;'
        u'+WinHttp.WinHttpRequest.5)')
    expected_msg_short = (
        u'GET /some/image/path/something.jpg '
        u'[ 10.10.10.100 > 10.10.10.100 : 80 ]')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = storage_writer.events[5]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-30 00:00:05')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.http_method, u'GET')
    self.assertEqual(event_object.http_status, 200)
    self.assertEqual(
        event_object.requested_uri_stem, u'/some/image/path/something.jpg')

    event_object = storage_writer.events[1]

    expected_msg = (
        u'GET /some/image/path/something.htm '
        u'[ 22.22.22.200 > 10.10.10.100 : 80 ] '
        u'HTTP Status: 404 '
        u'User Agent: Mozilla/5.0+(Macintosh;+Intel+Mac+OS+X+10_6_8)'
        u'+AppleWebKit/534.57.2+(KHTML,+like+Gecko)+Version/5.1.7'
        u'+Safari/534.57.2')
    expected_msg_short = (
        u'GET /some/image/path/something.htm '
        u'[ 22.22.22.200 > 10.10.10.100 : 80 ]')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  @shared_test_lib.skipUnlessHasTestFile([u'iis_without_date.log'])
  def testParseWithoutDate(self):
    """Tests the Parse function with logs without a date column."""
    parser_object = iis.WinIISParser()
    storage_writer = self._ParseFile([u'iis_without_date.log'], parser_object)

    self.assertEqual(len(storage_writer.events), 11)

    event_object = storage_writer.events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-30 00:00:03')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.protocol_version, u'HTTP/1.1')


if __name__ == '__main__':
  unittest.main()
