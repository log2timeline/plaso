#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the atlassian-jira.log parser."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import atlassian_jira

from tests.parsers.text_plugins import test_lib


class AtlassianJiraTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Jira application log parser."""

  def testParseTimeElementsInvalidInput(self):
    """Tests _ParseTimeElements raises ParseError on invalid input."""
    plugin = atlassian_jira.AtlassianJiraTextPlugin()

    # A tuple with an out-of-bounds month value should raise ParseError.
    with self.assertRaises(errors.ParseError):
      plugin._ParseTimeElements((2022, 13, 1, 0, 0, 0, 0))

  def testParseRecordUnknownKey(self):
    """Tests _ParseRecord raises ParseError on an unknown structure key."""
    plugin = atlassian_jira.AtlassianJiraTextPlugin()

    with self.assertRaises(errors.ParseError):
      plugin._ParseRecord(None, 'unknown_key', {})

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = atlassian_jira.AtlassianJiraTextPlugin()

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
    self.assertTrue(result)

    # A Confluence access log line should not match.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'[17/Jun/2021:12:57:26 +0200] user http-nio-8080-exec-6 '
        b'192.168.192.1 GET /index.action HTTP/1.1 200 1020ms 7881 '
        b'http://localhost/ Mozilla/5.0\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertFalse(result)

  def testParse(self):
    """Tests the Process function on a Jira application log file."""
    plugin = atlassian_jira.AtlassianJiraTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-jira.log'], plugin)

    num_event_data = storage_writer.GetNumberOfAttributeContainers('event_data')
    self.assertEqual(num_event_data, 7)

    num_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(num_warnings, 0)

    num_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(num_warnings, 0)

    # First entry: INFO level, [main] thread, start method.
    expected_event_values = {
        'body': (
            'Jira starting up. Version : 9.2.0, Mode : EAR, Build Number : '
            '904000, Build Date : 2022-08-25, Build UID : '
            'abc12345-dead-beef-cafe-1234567890ab'),
        'data_type': 'atlassian:jira:line',
        'level': 'INFO',
        'logger_class': 'com.atlassian.jira.startup.JiraStartupLogger',
        'logger_method': 'start',
        'thread': 'main',
        'written_time': '2022-10-03T09:00:01.042'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Second entry: INFO level, http-nio thread with hyphens and digits.
    expected_event_values = {
        'body': "Login attempted by user 'admin' from host '192.168.1.10'",
        'data_type': 'atlassian:jira:line',
        'level': 'INFO',
        'logger_class': 'com.atlassian.jira.web.filters.JiraLoginFilter',
        'logger_method': 'doFilter',
        'thread': 'http-nio-8080-exec-1',
        'written_time': '2022-10-03T09:00:45.317'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Third entry: WARN level, Caesium thread.
    expected_event_values = {
        'body': (
            "Lock 'CLUSTER_UPGRADE_LOCK' is held by node 'node1'. "
            "Cannot acquire."),
        'data_type': 'atlassian:jira:line',
        'level': 'WARN',
        'logger_class': 'com.atlassian.jira.cluster.ClusterManager',
        'logger_method': 'checkClusterLock',
        'thread': 'Caesium-1-4',
        'written_time': '2022-10-03T09:01:12.884'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Fourth entry: ERROR level, scheduler thread.
    expected_event_values = {
        'body': (
            "Failed to send notification email to 'user@example.com': "
            "Connection refused"),
        'data_type': 'atlassian:jira:line',
        'level': 'ERROR',
        'logger_class': 'com.atlassian.jira.mail.MailService',
        'logger_method': 'sendMail',
        'thread': 'scheduler_Worker-3',
        'written_time': '2022-10-03T09:02:33.501'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

    # Fifth entry: INFO level, AJP thread.
    expected_event_values = {
        'body': "Full re-index started by user 'admin'",
        'data_type': 'atlassian:jira:line',
        'level': 'INFO',
        'logger_class': 'com.atlassian.jira.issue.index.DefaultIndexManager',
        'logger_method': 'reIndexAll',
        'thread': 'AJP-bio-8009-exec-5',
        'written_time': '2022-10-03T09:05:00.999'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    # Sixth entry: DEBUG level.
    expected_event_values = {
        'body': 'No user found in session, returning null',
        'data_type': 'atlassian:jira:line',
        'level': 'DEBUG',
        'logger_class': (
            'com.atlassian.jira.security.JiraAuthenticationContext'),
        'logger_method': 'getLoggedInUser',
        'thread': 'http-nio-8080-exec-2',
        'written_time': '2022-10-03T09:07:11.123'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)

    # Seventh entry: FATAL level, <init> method (angle brackets in method name).
    expected_event_values = {
        'body': 'Fatal error during Jira startup: Out of memory',
        'data_type': 'atlassian:jira:line',
        'level': 'FATAL',
        'logger_class': 'com.atlassian.jira.startup.JiraStartupLogger',
        'logger_method': '<init>',
        'thread': 'main',
        'written_time': '2022-10-03T09:09:59.000'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 6)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
