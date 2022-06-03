#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Confluence access log parser."""

import unittest

from plaso.parsers import confluence_access

from tests.parsers import test_lib


class ConfluenceAccessUnitTest(test_lib.ParserTestCase):
  """Tests for Confluence access log parser."""

  def testParsePre711(self):
    """Tests the Parse function on a pre 7.11 access log."""
    parser = confluence_access.ConfluenceAccessParser()
    storage_writer = self._ParseFile(['confluence_access.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which parser generates events is nondeterministic hence
    # we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # 17/Jun/2021:12:57:26 +0200
    expected_event_values = {
        'data_type': 'confluence:access',
        'date_time': '2021-06-17 12:57:26',
        'http_request_referer': 'http://localhost/',
        'http_request_user_agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36'
            ' (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'),
        'http_response_code': 200,
        'http_response_bytes': 7881,
        'remote_name': '192.168.192.1',
        'user_name': 'user',
        'http_version': 'HTTP/1.1',
        'process_duration': 1020,
        'http_request_method': 'GET',
        'http_request_uri': '/index.action',
        'thread_name': 'http-nio-8080-exec-6',
        'forwarded_for': None
    }

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParsePost711(self):
    """Tests the Parse function on a post 7.11 access log."""
    parser = confluence_access.ConfluenceAccessParser()
    storage_writer = self._ParseFile(['confluence_access_post7.11.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which parser generates events is nondeterministic hence
    # we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # 17/Jun/2021:12:57:26 +0200
    expected_event_values = {
        'data_type': 'confluence:access',
        'date_time': '2021-06-17 12:57:26',
        'http_request_referer': 'http://localhost/',
        'http_request_user_agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36'
            ' (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'),
        'http_response_code': 200,
        'http_response_bytes': 7881,
        'remote_name': '0:0:0:0:0:0:0:1',
        'user_name': 'testuser',
        'http_version': 'HTTP/1.1',
        'process_duration': 1020,
        'http_request_method': 'GET',
        'http_request_uri': '/index.action',
        'thread_name': 'http-nio-8080-exec-6',
        'forwarded_for': '192.168.1.15'
    }

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

if __name__ == '__main__':
  unittest.main()
