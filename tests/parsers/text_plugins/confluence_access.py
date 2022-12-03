#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Confluence access log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import confluence_access

from tests.parsers.text_plugins import test_lib


class ConfluenceAccessTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Confluence access log text parser plugin."""

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
