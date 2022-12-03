#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the PostgreSQL application log file text parser plugin."""

import unittest

from plaso.parsers.text_plugins import postgresql

from tests.parsers.text_plugins import test_lib


class PostgreSQLTextPluginTest(test_lib.TextPluginTestCase):
  """the PostgreSQL application log file text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = postgresql.PostgreSQLTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['postgresql.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 20)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test a regular log entry.
    expected_event_values = {
        'data_type': 'postgresql:application_log:entry',
        'log_line': (
            'starting PostgreSQL 12.9 (Ubuntu 12.9-0ubuntu0.20.04.1) '
            'on x86_64-pc-linux-gnu, compiled by gcc '
            '(Ubuntu 9.3.0-17ubuntu1~20.04) 9.3.0, 64-bit'),
        'pid': '7755',
        'recorded_time': '2022-04-12T00:16:05.526+00:00',
        'severity': 'LOG'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test a log entry containing user and database.
    expected_event_values = {
        'data_type': 'postgresql:application_log:entry',
        'log_line': 'password authentication failed for user "postgres"',
        'pid': '9158',
        'recorded_time': '2022-04-12T00:24:24.741+00:00',
        'severity': 'FATAL',
        'user': 'postgres@postgres'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 15)
    self.CheckEventData(event_data, expected_event_values)

    # Check a multi-line log entry.
    expected_event_values = {
        'data_type': 'postgresql:application_log:entry',
        'log_line': (
            'User "postgres" has no password assigned.\n        '
            'Connection matched pg_hba.conf line 96: '
            '"host    all             all             '
            '127.0.0.1/32            md5"'),
        'pid': '9158',
        'recorded_time': '2022-04-12T00:24:24.741+00:00',
        'severity': 'DETAIL'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 16)
    self.CheckEventData(event_data, expected_event_values)

    # Check a log entry with a time zone.
    expected_event_values = {
        'data_type': 'postgresql:application_log:entry',
        'log_line': (
            'could not receive data from client: Connection reset by peer'),
        'pid': '203851-1',
        'recorded_time': '2022-07-15T23:04:27',
        'severity': 'LOG'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 19)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
