#!/usr/bin/env python3
"""Tests for Confluence access log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import confluence_access

from tests.parsers.text_plugins import test_lib


class ConfluenceAccessTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Confluence access log text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat function."""
    plugin = confluence_access.ConfluenceAccessTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    # Check pre 7.11 format.
    file_object = io.BytesIO(
        b'[17/Jun/2021:12:57:26 +0200] user http-nio-8080-exec-6 '
        b'192.168.192.1 GET /index.action HTTP/1.1 200 1020ms 7881 '
        b'http://localhost/ Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) '
        b'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 '
        b'Safari/537.36\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check post 7.11 format.
    file_object = io.BytesIO(
        b'[17/Jun/2021:12:57:26 +0200] 192.168.1.15 testuser '
        b'http-nio-8080-exec-6 0:0:0:0:0:0:0:1 GET /index.action HTTP/1.1 '
        b'200 1020ms 7881 http://localhost/ Mozilla/5.0 (Macintosh; Intel '
        b'Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) '
        b'Chrome/87.0.4280.88 Safari/537.36\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_object = io.BytesIO(
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testProcessWithPre711AccessLog(self):
    """Tests the Process function with a pre 7.11 access log."""
    plugin = confluence_access.ConfluenceAccessTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['confluence_access.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'confluence:access',
        'forwarded_for': None,
        'http_request_referer': 'http://localhost/',
        'http_request_method': 'GET',
        'http_request_uri': '/index.action',
        'http_response_bytes': 7881,
        'http_response_code': 200,
        'http_request_user_agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 '
            'Safari/537.36'),
        'http_version': 'HTTP/1.1',
        'process_duration': 1020,
        'recorded_time': '2021-06-17T12:57:26+02:00',
        'remote_name': '192.168.192.1',
        'thread_name': 'http-nio-8080-exec-6',
        'user_name': 'user'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWithPost711AccessLog(self):
    """Tests the Process function with a post 7.11 access log."""
    plugin = confluence_access.ConfluenceAccessTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['confluence_access_post7.11.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'confluence:access',
        'forwarded_for': '192.168.1.15',
        'http_request_referer': 'http://localhost/',
        'http_request_method': 'GET',
        'http_request_uri': '/index.action',
        'http_response_bytes': 7881,
        'http_response_code': 200,
        'http_request_user_agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 '
            'Safari/537.36'),
        'http_version': 'HTTP/1.1',
        'process_duration': 1020,
        'recorded_time': '2021-06-17T12:57:26+02:00',
        'remote_name': '0:0:0:0:0:0:0:1',
        'thread_name': 'http-nio-8080-exec-6',
        'user_name': 'testuser'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
