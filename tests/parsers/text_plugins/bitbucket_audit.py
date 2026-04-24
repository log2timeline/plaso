#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Atlassian Bitbucket audit log text parser plugin."""

import unittest

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
    self.assertEqual(number_of_event_data, 4)

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


if __name__ == '__main__':
  unittest.main()
