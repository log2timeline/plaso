#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for PostgreSQL log parser"""

import unittest

from plaso.parsers import postgresql
from tests.parsers import test_lib


class PostgreSQLParserTest(test_lib.ParserTestCase):
  """Tests for the PostgreSQL log parser"""

  def testParse(self):
    """Tests the parse function on an example file."""
    parser = postgresql.PostgreSQLParser()
    storage_writer = self._ParseFile(['postgresql.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 20)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Regular line
    expected_event_values = {
        'pid': '7755',
        'log_level': 'LOG',
        'log_line': 'starting PostgreSQL 12.9 (Ubuntu 12.9-0ubuntu0.20.04.1) '
                    'on x86_64-pc-linux-gnu, compiled by gcc '
                    '(Ubuntu 9.3.0-17ubuntu1~20.04) 9.3.0, 64-bit'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # User and database
    expected_event_values = {
        'pid': '9158',
        'log_level': 'FATAL',
        'user': 'postgres@postgres',
        'log_line': 'password authentication failed for user "postgres"'}

    self.CheckEventValues(storage_writer, events[15], expected_event_values)

    # Multiline
    expected_event_values = {
        'pid': '9158',
        'log_level': 'DETAIL',
        'log_line': 'User "postgres" has no password assigned.\n        '
                    'Connection matched pg_hba.conf line 96: '
                    '"host    all             all             '
                    '127.0.0.1/32            md5"'}

    self.CheckEventValues(storage_writer, events[16], expected_event_values)

    # Other time zone
    expected_event_values = {
        'pid': '203851-1',
        'log_level': 'LOG',
        'log_line': 'could not receive data from client: '
                    'Connection reset by peer'}

    self.CheckEventValues(storage_writer, events[19], expected_event_values)

if __name__ == '__main__':
  unittest.main()
