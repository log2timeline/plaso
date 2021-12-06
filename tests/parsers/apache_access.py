#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Apache access log parser."""

import unittest

from plaso.containers import warnings
from plaso.parsers import apache_access

from tests.parsers import test_lib


class ApacheAccessUnitTest(test_lib.ParserTestCase):
  """Tests for Apache access log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = apache_access.ApacheAccessParser()
    storage_writer = self._ParseFile(['access.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 14)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which parser generates events is nondeterministic hence
    # we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # Test combined log format event.
    # 13/Jan/2016:19:31:20 +0200
    expected_event_values = {
        'data_type': 'apache:access',
        'date_time': '2016-01-13 19:31:20',
        'http_request': (
            'GET /wp-content/themes/darkmode/evil.php?cmd=uname+-a HTTP/1.1'),
        'http_request_referer': 'http://localhost/',
        'http_request_user_agent': (
            'Mozilla/5.0 (X11; Linux i686; rv:2.0b12pre) Gecko/20100101 '
            'Firefox/4'),
        'http_response_code': 200,
        'http_response_bytes': 694,
        'ip_address': '192.168.0.2',
        'remote_name': '-',
        'timestamp': '2016-01-13 17:31:20.000000',
        'user_name': '-'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Test common log format parser event.
    expected_event_values = {
        'data_type': 'apache:access',
        'date_time': '2016-01-13 19:31:16',
        'http_request': (
            'GET /wp-content/themes/darkmode/header.php?install2 HTTP/1.1'),
        'http_response_code': 200,
        'http_response_bytes': 494,
        'ip_address': '10.0.0.1',
        'remote_name': '-',
        'user_name': '-'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # Test an extraction warning.
    generator = storage_writer.GetAttributeContainers(
        warnings.ExtractionWarning.CONTAINER_TYPE)

    test_warnings = list(generator)
    test_warning = test_warnings[0]

    expected_message = (
        'unable to parse log line: "46.118.127.106 - - [20/May/2015:12:05:17 '
        '+0000] "GET /scripts/grok-py-test/co..." at offset: 1589')
    self.assertEqual(test_warning.message, expected_message)
    self.assertEqual(test_warning.parser_chain, 'apache_access')

    # Test vhost_combined log format event.
    expected_event_values = {
        'data_type': 'apache:access',
        'date_time': '2018-01-13 19:31:17',
        'http_request': 'GET /wp-content/themes/darkmode/evil.php HTTP/1.1',
        'http_request_referer': '-',
        'http_request_user_agent': (
            'Mozilla/5.0 (Windows NT 7.1) AppleWebKit/534.30 (KHTML, like '
            'Gecko) Chrome/12.0.742.112 Safari/534.30'),
        'http_response_code': 200,
        'http_response_bytes': 1063,
        'ip_address': '192.168.0.2',
        'port_number': 443,
        'remote_name': '-',
        'server_name': 'plaso.log2timeline.net',
        'user_name': '-'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

    # Test common log format parser event with Kerberos user name
    expected_event_values = {
        'data_type': 'apache:access',
        'date_time': '2019-11-16 09:46:42',
        'http_request': ('GET / HTTP/1.1'),
        'http_response_code': 200,
        'http_response_bytes': 8264,
        'ip_address': '192.168.0.64',
        'remote_name': '-',
        'user_name': 'pyllyukko@EXAMPLE.COM'}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)


if __name__ == '__main__':
  unittest.main()
