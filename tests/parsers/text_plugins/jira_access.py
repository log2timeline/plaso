#!/usr/bin/env python3
"""Tests for Jira access log text parser plugin."""

import io
import unittest

from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import jira_access

from tests.parsers.text_plugins import test_lib


class JiraAccessTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Jira access log text parser plugin."""

  # pylint: disable=protected-access

  def testParseTimeElementsInvalidInput(self):
    """Tests _ParseTimeElements raises ParseError on invalid input."""
    plugin = jira_access.JiraAccessTextPlugin()

    with self.assertRaises(errors.ParseError):
      plugin._ParseTimeElements(None)

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = jira_access.JiraAccessTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    # Check pre 9.4 format.
    file_object = io.BytesIO(
        b'[03/Oct/2022:09:00:01 +0000] admin http-nio-8080-exec-1 '
        b'192.168.1.10 GET /secure/Dashboard.jspa HTTP/1.1 200 350ms '
        b'12345 http://localhost/ Mozilla/5.0\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check post 9.4 format (with X-Forwarded-For).
    file_object = io.BytesIO(
        b'[03/Oct/2022:09:00:01 +0000] 10.0.0.5 admin '
        b'http-nio-8080-exec-1 192.168.1.10 GET /secure/Dashboard.jspa '
        b'HTTP/1.1 200 350ms 12345 http://localhost/ Mozilla/5.0\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check unsupported date and time value.
    file_object = io.BytesIO(
        b'[99/Oct/2022:09:00:01 +0000] admin http-nio-8080-exec-1 '
        b'192.168.1.10 GET /secure/Dashboard.jspa HTTP/1.1 200 350ms '
        b'12345 http://localhost/ Mozilla/5.0\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_object = io.BytesIO(
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testProcessWithMonths(self):
    """Tests the Process function and check month abbreviations."""
    plugin = jira_access.JiraAccessTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['jira_access_months.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 12)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_times = [
        '2022-01-01T10:00:00+00:00',
        '2022-02-01T10:00:00+00:00',
        '2022-03-01T10:00:00+00:00',
        '2022-04-01T10:00:00+00:00',
        '2022-05-01T10:00:00+00:00',
        '2022-06-01T10:00:00+00:00',
        '2022-07-01T10:00:00+00:00',
        '2022-08-01T10:00:00+00:00',
        '2022-09-01T10:00:00+00:00',
        '2022-10-01T10:00:00+00:00',
        '2022-11-01T10:00:00+00:00',
        '2022-12-01T10:00:00+00:00']

    for index, expected_time in enumerate(expected_times):
      event_data = storage_writer.GetAttributeContainerByIndex(
          'event_data', index)
      self.CheckEventData(event_data, {'recorded_time': expected_time})

  def testProcessWithPre94AccessLog(self):
    """Tests the Process function with a pre 9.4 access log."""
    plugin = jira_access.JiraAccessTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['jira_access.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'jira:access',
        'forwarded_for': None,
        'http_request_method': 'GET',
        'http_request_referer': 'http://localhost/',
        'http_request_uri': '/secure/Dashboard.jspa',
        'http_request_user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 '
            'Safari/537.36'),
        'http_response_bytes': 12345,
        'http_response_code': 200,
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
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'jira:access',
        'forwarded_for': '10.0.0.5',
        'http_request_method': 'GET',
        'http_request_referer': 'http://localhost/',
        'http_request_uri': '/secure/Dashboard.jspa',
        'http_request_user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 '
            'Safari/537.36'),
        'http_response_bytes': 12345,
        'http_response_code': 200,
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
