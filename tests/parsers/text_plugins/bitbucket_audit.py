#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Atlassian Bitbucket audit log text parser plugin."""

import unittest
import unittest.mock

from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import bitbucket_audit

from tests.parsers.text_plugins import test_lib


class BitbucketAuditTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Bitbucket audit log text parser plugin."""

  def testParse(self):
    """Tests the Process function."""
    plugin = bitbucket_audit.BitbucketAuditTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-bitbucket-audit.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # First entry: RestrictedRefAddedEvent with JSON details.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:audit',
        'details': (
            '{"id":1,"value":"refs/heads/random-cleanups","users":["user"]}'),
        'entity': 'BITBUCKET/bitbucket',
        'event_name': 'RestrictedRefAddedEvent',
        'recorded_time': '2014-05-21T14:09:21.906+00:00',
        'remote_address': '0:0:0:0:0:0:0:1',
        'request_id': '@8KJQAGx969x538x0',
        'session_id': '6ywzi6',
        'user_name': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Second entry: RestrictedRefRemovedEvent.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:audit',
        'details': '{"id":1,"value":"refs/heads/random-cleanups"}',
        'entity': 'BITBUCKET/bitbucket',
        'event_name': 'RestrictedRefRemovedEvent',
        'recorded_time': '2014-05-21T14:09:25.418+00:00',
        'remote_address': '0:0:0:0:0:0:0:1',
        'request_id': '@8KJQAGx969x540x0',
        'session_id': '6ywzi6',
        'user_name': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Third entry: RepositoryCreatedEvent with forwarded IP.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:audit',
        'details': (
            '{"id":2,"name":"my-repo","project":{"key":"myproject"}}'),
        'entity': 'PROJECT/myproject',
        'event_name': 'RepositoryCreatedEvent',
        'recorded_time': '2014-05-21T14:09:33.433+00:00',
        'remote_address': '63.246.22.199,172.16.1.187',
        'request_id': '@8KJQAGx969x543x0',
        'session_id': 'tmpqqw',
        'user_name': 'jsmith'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Fourth entry: minimal entry with dash placeholders.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:audit',
        'details': None,
        'entity': None,
        'event_name': 'UserCreatedEvent',
        'recorded_time': '2014-05-21T14:10:00.000+00:00',
        'remote_address': '10.1.1.100',
        'request_id': None,
        'session_id': None,
        'user_name': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

    # Fifth entry: user_name is '-' → None (covers the None branch).
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:audit',
        'details': None,
        'entity': None,
        'event_name': 'UserLoggedInEvent',
        'recorded_time': '2014-05-21T14:10:10.000+00:00',
        'remote_address': '10.1.1.100',
        'request_id': None,
        'session_id': None,
        'user_name': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)


  def _CheckRequiredFormat(self, plugin, path_segments):
    """Helper to call CheckRequiredFormat on a test file."""
    parser_mediator = parsers_mediator.ParserMediator()
    storage_writer = self._CreateStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)
    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator.SetFileEntry(file_entry)
    parser_mediator.AppendToParserChain('text')
    encoding = plugin.ENCODING or parser_mediator.GetCodePage()
    file_object = file_entry.GetFileObject()
    text_reader_obj = text_parser.EncodedTextReader(
        file_object, encoding=encoding)
    text_reader_obj.ReadLines()
    return plugin.CheckRequiredFormat(parser_mediator, text_reader_obj)

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = bitbucket_audit.BitbucketAuditTextPlugin()

    # Non-audit-log file (syslog) should be rejected.
    self.assertFalse(
        self._CheckRequiredFormat(plugin, ['syslog', 'syslog']))

  def testParseErrors(self):
    """Tests _ParseRecord and CheckRequiredFormat error paths."""
    plugin = bitbucket_audit.BitbucketAuditTextPlugin()

    # _ParseRecord raises ParseError on unknown key.
    with self.assertRaises(errors.ParseError):
      plugin._ParseRecord(  # pylint: disable=protected-access
          None, 'unknown_key', {})

    # CheckRequiredFormat rejects a file with an out-of-range timestamp
    # (year 1970 = timestamp 0, which is before the 2000 cutoff).
    text_reader = unittest.mock.Mock()
    text_reader.lines = (
        '0:0:0:0:0:0:0:1 | RestrictedRefAddedEvent | admin | 0 | '
        'BITBUCKET/bitbucket | {} | @req | session')
    self.assertFalse(plugin.CheckRequiredFormat(
        unittest.mock.Mock(), text_reader))

    # CheckRequiredFormat rejects when _VerifyString fails (non-matching file).
    text_reader2 = unittest.mock.Mock()
    text_reader2.lines = 'Jan 22 07:52:33 hostname sshd[123]: connection'
    self.assertFalse(plugin.CheckRequiredFormat(
        unittest.mock.Mock(), text_reader2))


if __name__ == '__main__':
  unittest.main()
