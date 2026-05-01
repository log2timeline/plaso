#!/usr/bin/env python3
"""Tests for Jira access log text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import jira_access

from tests.parsers.text_plugins import test_lib


class JiraAccessTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Jira access log text parser plugin."""

  def testParseTimeElementsInvalidInput(self):
    """Tests _ParseTimeElements raises ParseError on invalid input."""
    plugin = jira_access.JiraAccessTextPlugin()

    with self.assertRaises(errors.ParseError):
      plugin._ParseTimeElements(None)  # pylint: disable=protected-access

  def testProcessMonths(self):
    """Tests all month abbreviations are parsed correctly."""
    plugin = jira_access.JiraAccessTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['jira_access_months.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 11)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_times = [
        '2022-01-01T10:00:00+00:00',  # Jan
        '2022-02-01T10:00:00+00:00',  # Feb
        '2022-03-01T10:00:00+00:00',  # Mar
        '2022-04-01T10:00:00+00:00',  # Apr
        '2022-05-01T10:00:00+00:00',  # May
        '2022-06-01T10:00:00+00:00',  # Jun
        '2022-07-01T10:00:00+00:00',  # Jul
        '2022-08-01T10:00:00+00:00',  # Aug
        '2022-09-01T10:00:00+00:00',  # Sep
        '2022-11-01T10:00:00+00:00',  # Nov
        '2022-12-01T10:00:00+00:00',  # Dec
    ]

    for index, expected_time in enumerate(expected_times):
      event_data = storage_writer.GetAttributeContainerByIndex(
          'event_data', index)
      self.CheckEventData(event_data, {'recorded_time': expected_time})

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = jira_access.JiraAccessTextPlugin()

    # Pre-9.4 format line should match.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'[03/Oct/2022:09:00:01 +0000] admin http-nio-8080-exec-1 '
        b'192.168.1.10 GET /secure/Dashboard.jspa HTTP/1.1 200 350ms '
        b'12345 http://localhost/ Mozilla/5.0\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

    # Post-9.4 format line (with X-Forwarded-For) should also match.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'[03/Oct/2022:09:00:01 +0000] 10.0.0.5 admin '
        b'http-nio-8080-exec-1 192.168.1.10 GET /secure/Dashboard.jspa '
        b'HTTP/1.1 200 350ms 12345 http://localhost/ Mozilla/5.0\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

    # A line with an invalid hour (25) passes grammar but fails time parsing.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'[03/Oct/2022:25:00:01 +0000] admin http-nio-8080-exec-1 '
        b'192.168.1.10 GET /secure/Dashboard.jspa HTTP/1.1 200 350ms '
        b'12345 http://localhost/ Mozilla/5.0\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

    # A Jira application log line should not match.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'2022-10-03 09:00:01,042 INFO [main] '
        b'[com.atlassian.jira.startup.JiraStartupLogger] start '
        b'Jira starting up.\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

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

    # First entry: authenticated user, GET, IPv4 remote, +0000 timezone.
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

    # Second entry: anonymous user (-), GET, REST API URI.
    expected_event_values = {
        'data_type': 'jira:access',
        'forwarded_for': None,
        'http_request_method': 'GET',
        'http_request_referer': 'http://localhost/browse/PROJ-1',
        'http_request_uri': '/rest/api/2/issue/PROJ-1',
        'http_request_user_agent': (
            'Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 '
            'Safari/537.36'),
        'http_response_bytes': 4201,
        'http_response_code': 200,
        'http_version': 'HTTP/1.1',
        'process_duration': 98,
        'recorded_time': '2022-10-03T09:00:15+00:00',
        'remote_name': '192.168.1.11',
        'thread_name': 'http-nio-8080-exec-2',
        'user_name': '-'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Third entry: POST, IPv6 remote, 302 redirect, 0 response bytes.
    expected_event_values = {
        'data_type': 'jira:access',
        'forwarded_for': None,
        'http_request_method': 'POST',
        'http_request_referer': 'http://localhost/secure/Dashboard.jspa',
        'http_request_uri': '/secure/QuickCreateIssue.jspa',
        'http_request_user_agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 '
            'Safari/537.36'),
        'http_response_bytes': 0,
        'http_response_code': 302,
        'http_version': 'HTTP/1.1',
        'process_duration': 512,
        'recorded_time': '2022-10-03T09:01:30+00:00',
        'remote_name': '0:0:0:0:0:0:0:1',
        'thread_name': 'http-nio-8080-exec-3',
        'user_name': 'jdoe'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Fourth entry: DELETE, negative timezone offset (-0500), dash response
    # bytes.
    expected_event_values = {
        'data_type': 'jira:access',
        'forwarded_for': None,
        'http_request_method': 'DELETE',
        'http_request_referer': 'http://localhost/browse/PROJ-2',
        'http_request_uri': '/rest/api/2/issue/PROJ-2',
        'http_request_user_agent': (
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1)'),
        'http_response_bytes': '-',
        'http_response_code': 204,
        'http_version': 'HTTP/1.1',
        'process_duration': 77,
        'recorded_time': '2022-10-03T09:02:00-05:00',
        'remote_name': '192.168.1.12',
        'thread_name': 'http-nio-8080-exec-4',
        'user_name': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
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

    # First entry: with X-Forwarded-For, authenticated user.
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

    # Second entry: with X-Forwarded-For, anonymous user, positive non-UTC
    # timezone offset (+0100), curl user agent.
    expected_event_values = {
        'data_type': 'jira:access',
        'forwarded_for': '10.0.0.6',
        'http_request_method': 'GET',
        'http_request_referer': 'http://localhost/',
        'http_request_uri': '/login.jsp',
        'http_request_user_agent': 'curl/7.85.0',
        'http_response_bytes': 8712,
        'http_response_code': 200,
        'http_version': 'HTTP/1.1',
        'process_duration': 125,
        'recorded_time': '2022-10-03T09:00:30+01:00',
        'remote_name': '192.168.1.11',
        'thread_name': 'http-nio-8080-exec-2',
        'user_name': '-'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
