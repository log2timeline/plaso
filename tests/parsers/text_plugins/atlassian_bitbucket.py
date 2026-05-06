#!/usr/bin/env python3
"""Tests for the Atlassian Bitbucket application log text parser plugin."""

import io
import unittest

from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import atlassian_bitbucket

from tests.parsers.text_plugins import test_lib


class AtlassianBitbucketTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Bitbucket application log text parser plugin."""

  # pylint: disable=protected-access

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = atlassian_bitbucket.AtlassianBitbucketTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    # Check non-matching syslog.
    file_entry = self._GetTestFileEntry(['syslog', 'syslog'])
    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching Confluence log.
    file_entry = self._GetTestFileEntry(['atlassian-confluence.log'])
    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check when only 1 line matches but 2 are expected.
    file_object = io.BytesIO(
        b'2020-09-08 07:53:45,084 INFO [main] '
        b'com.atlassian.bitbucket.internal.boot.log.BuildInfoLogger '
        b'Starting Bitbucket 7.4.0\n'
        b'Jan 22 07:52:33 not-a-bitbucket-line\n')
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check when when first non-empty line does not match verification grammar.
    file_object = io.BytesIO(
        b'\n'
        b'Jan 22 07:52:33 hostname sshd[123]: connection\n'
        b'2020-09-08 07:53:45,084 INFO [main] '
        b'com.atlassian.bitbucket.log.Logger Starting\n')
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testParse(self):
    """Tests the Process function."""
    plugin = atlassian_bitbucket.AtlassianBitbucketTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-bitbucket.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # First entry: simple INFO line, no request context.
    expected_event_values = {
        'body': (
            'Starting Bitbucket 7.4.0 (204e35a built on Tue Jul 07 14:31:59 '
            'NZST 2020)'),
        'data_type': 'atlassian:bitbucket:line',
        'ip_address': None,
        'level': 'INFO',
        'logger_class': (
            'com.atlassian.bitbucket.internal.boot.log.BuildInfoLogger'),
        'request_action': None,
        'request_identifier': None,
        'session_identifier': None,
        'thread': 'main',
        'user_name': None,
        'written_time': '2020-09-08T07:53:45.084'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Second entry: INFO line with full request context fields.
    expected_event_values = {
        'body': (
            'Repository 0030-8a2a778e2d97e278f541-5 has been created and '
            'configured successfully'),
        'data_type': 'atlassian:bitbucket:line',
        'ip_address': '10.229.31.195',
        'level': 'INFO',
        'logger_class': 'c.a.b.m.r.DefaultRepositoryManager',
        'request_action': 'TransactionService/Transact',
        'request_identifier': '2CM38K4Fx339x113x2',
        'session_identifier': '@5XDWX5x339x568x0,4SJOMSOBx339x40x2',
        'thread': 'tx:thread-2',
        'user_name': 'admin',
        'written_time': '2022-04-12T05:39:57.408'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Third entry: INFO with partial request context (no comma-separated
    # session ID).
    expected_event_values = {
        'body': (
            '[p/0030/h/8a2a778e2d97e278f541/r/5] Repair from mesh2@2 '
            'completed in 238 ms'),
        'data_type': 'atlassian:bitbucket:line',
        'ip_address': '10.229.31.65',
        'level': 'INFO',
        'logger_class': 'c.a.b.m.repair.DefaultRepairManager',
        'request_action': 'ManagementService/RepairRepository',
        'request_identifier': '2CM38K4Fx339x114x2',
        'session_identifier': '@5XDWX5x339x568x0',
        'thread': 'grpc-server:thread-16',
        'user_name': 'admin',
        'written_time': '2022-04-12T05:39:57.766'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Fourth entry: WARN with no request context.
    expected_event_values = {
        'body': (
            'Cannot scan directory /extension/build-status/ in bundle '
            'com.atlassian.bitbucket.server.bitbucket-frontend; it does not '
            'exist'),
        'data_type': 'atlassian:bitbucket:line',
        'ip_address': None,
        'level': 'WARN',
        'logger_class': 'c.a.s.i.p.s.OsgiBundledPathScanner',
        'request_action': None,
        'request_identifier': None,
        'session_identifier': None,
        'thread': 'spring-startup',
        'user_name': None,
        'written_time': '2022-12-01T14:03:28.717'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

    # Fifth entry: DEBUG with full logger class name.
    expected_event_values = {
        'body': (
            'delete sta_activity_0 from sta_activity sta_activity_0 inner '
            'join HT_sta_pr_rescope_activity HT_sta_pr_rescope_activity_0 on '
            'sta_activity_0.id=HT_sta_pr_rescope_activity_0.activity_id'),
        'data_type': 'atlassian:bitbucket:line',
        'ip_address': None,
        'level': 'DEBUG',
        'logger_class': 'org.hibernate.SQL',
        'request_action': None,
        'request_identifier': None,
        'session_identifier': None,
        'thread': 'clusterScheduler_Worker-8',
        'user_name': None,
        'written_time': '2014-12-04T19:39:39.749'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

  def testParseRecord(self):
    """Tests the _ParseRecord function."""
    plugin = atlassian_bitbucket.AtlassianBitbucketTextPlugin()

    with self.assertRaises(errors.ParseError):
      plugin._ParseRecord(None, 'unknown_key', {})

  def testParseTimeElements(self):
    """Tests the _ParseTimeElements function."""
    plugin = atlassian_bitbucket.AtlassianBitbucketTextPlugin()

    with self.assertRaises(errors.ParseError):
      plugin._ParseTimeElements('invalid')


if __name__ == '__main__':
  unittest.main()
