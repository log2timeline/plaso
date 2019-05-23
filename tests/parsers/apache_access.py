#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for apache access log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import apache_access as _  # pylint: disable=unused-import
from plaso.parsers import apache_access

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class ApacheAccessUnitTest(test_lib.ParserTestCase):
  """Tests for apache access log parser."""

  @shared_test_lib.skipUnlessHasTestFile(['access.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = apache_access.ApacheAccessParser()
    storage_writer = self._ParseFile(['access.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 7)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # Test combined log format event.
    event = events[2]
    self.CheckTimestamp(event.timestamp, '2016-01-13 17:31:20.000000')

    self.assertEqual(event.ip_address, '192.168.0.2')
    self.assertEqual(event.remote_name, '-')
    self.assertEqual(event.user_name, '-')

    self.assertEqual(
        event.http_request,
        'GET /wp-content/themes/darkmode/evil.php?cmd=uname+-a HTTP/1.1')

    self.assertEqual(event.http_response_code, 200)
    self.assertEqual(event.http_response_bytes, 694)
    self.assertEqual(event.http_request_referer, 'http://localhost/')

    self.assertEqual(
        event.http_request_user_agent,
        'Mozilla/5.0 (X11; Linux i686; rv:2.0b12pre) Gecko/20100101 Firefox/4')

    expected_message = (
        'http_request: GET /wp-content/themes/darkmode/evil.php?cmd=uname+-a '
        'HTTP/1.1 from: 192.168.0.2 code: 200 referer: http://localhost/ '
        'user_agent: Mozilla/5.0 (X11; Linux i686; rv:2.0b12pre) '
        'Gecko/20100101 Firefox/4'
    )

    expected_short_message = (
        'GET /wp-content/themes/darkmode/evil.php?cmd=uname+-a HTTP/1.1 from: '
        '192.168.0.2'
    )

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test common log format parser event.
    event = events[3]
    self.CheckTimestamp(event.timestamp, '2016-01-13 19:31:16.000000')

    self.assertEqual(event.ip_address, '10.0.0.1')
    self.assertEqual(event.remote_name, '-')
    self.assertEqual(event.user_name, '-')

    self.assertEqual(
        event.http_request,
        'GET /wp-content/themes/darkmode/header.php?install2 HTTP/1.1')

    self.assertEqual(event.http_response_code, 200)
    self.assertEqual(event.http_response_bytes, 494)

    expected_message = (
        'http_request: GET /wp-content/themes/darkmode/header.php?install2 '
        'HTTP/1.1 from: 10.0.0.1 code: 200'
    )

    expected_short_message = (
        'GET /wp-content/themes/darkmode/header.php?install2 HTTP/1.1 from: '
        '10.0.0.1'
    )

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test the extraction warning.
    warnings = list(storage_writer.GetWarnings())
    warning = warnings[0]

    self.assertEqual(warning.message, (
        'unable to parse log line: "46.118.127.106 - - [20/May/2015:12:05:17 '
        '+0000] "GET /scripts/grok-py-test/co..." at offset: 1589'))
    self.assertEqual(warning.parser_chain, 'apache_access')


if __name__ == '__main__':
  unittest.main()
