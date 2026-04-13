#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Jira access log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import jira_access

from tests.parsers.text_plugins import test_lib


class JiraAccessTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Jira access log text parser plugin."""

  def testProcessWithPre94AccessLog(self):
    """Tests the Process function with a pre 9.4 access log."""
    plugin = jira_access.JiraAccessTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['jira_access.log'], plugin)

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
        'data_type': 'jira:access',
        'forwarded_for': None,
        'http_request_referer': 'http://localhost/',
        'http_request_method': 'GET',
        'http_request_uri': '/secure/Dashboard.jspa',
        'http_response_bytes': 12345,
        'http_response_code': 200,
        'http_request_user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 '
            'Safari/537.36'),
        'http_version': 'HTTP/1.1',
        'process_duration': 350,
        'recorded_time': '2022-10-03T09:00:01+00:00',
        'remote_name': '192.168.1.10',
        'thread_name': 'http-nio-8080-exec-1',
        'user_name': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWithPost94AccessLog(self):
    """Tests the Process function with a post 9.4 access log."""
    plugin = jira_access.JiraAccessTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['jira_access_post9.4.log'], plugin)

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
        'data_type': 'jira:access',
        'forwarded_for': '10.0.0.5',
        'http_request_referer': 'http://localhost/',
        'http_request_method': 'GET',
        'http_request_uri': '/secure/Dashboard.jspa',
        'http_response_bytes': 12345,
        'http_response_code': 200,
        'http_request_user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 '
            'Safari/537.36'),
        'http_version': 'HTTP/1.1',
        'process_duration': 350,
        'recorded_time': '2022-10-03T09:00:01+00:00',
        'remote_name': '192.168.1.10',
        'thread_name': 'http-nio-8080-exec-1',
        'user_name': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
