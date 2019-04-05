#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the 4n6time MySQL output class."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso import formatters   # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import mysql_4n6time

from tests.output import fake_mysqldb
from tests.output import test_lib

if mysql_4n6time.MySQLdb is None:
  mysql_4n6time.MySQLdb = fake_mysqldb


class MySQL4n6TimeTestEvent(events.EventObject):
  """Test event."""

  DATA_TYPE = 'syslog:line'

  def __init__(self, event_timestamp):
    """Initializes an event."""
    super(MySQL4n6TimeTestEvent, self).__init__()
    self.display_name = 'log/syslog.1'
    self.filename = 'log/syslog.1'
    self.hostname = 'ubuntu'
    self.my_number = 123
    self.some_additional_foo = True
    self.text = (
        'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        'closed for user root)')
    self.timestamp_desc = definitions.TIME_DESCRIPTION_WRITTEN
    self.timestamp = event_timestamp


class MySQL4n6TimeOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the 4n6time MySQL output class."""

  # pylint: disable=protected-access

  def testGetTags(self):
    """Tests the _GetTags function."""
    fake_cursor = fake_mysqldb.FakeMySQLdbCursor()
    fake_cursor.expected_query = 'SELECT DISTINCT tag FROM log2timeline'
    fake_cursor.query_results = [('one',), ('two,three',), ('four',)]

    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)
    output_module._cursor = fake_cursor

    expected_tags = ['one', 'two', 'three', 'four']
    tags = output_module._GetTags()
    self.assertEqual(tags, expected_tags)

  def testGetUniqueValues(self):
    """Tests the _GetUniqueValues function."""
    fake_cursor = fake_mysqldb.FakeMySQLdbCursor()
    fake_cursor.expected_query = (
        'SELECT source, COUNT(source) FROM log2timeline GROUP BY source')
    fake_cursor.query_results = [('one', 1), ('two', 2), ('three', 3)]

    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)
    output_module._cursor = fake_cursor

    expected_unique_values = {'one': 1, 'two': 2, 'three': 3}
    unique_values = output_module._GetUniqueValues('source')
    self.assertEqual(unique_values, expected_unique_values)

  # TODO: add test for Open and Close

  def testGetSanitizedEventValues(self):
    """Tests the GetSanitizedEventValues function."""
    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)

    expected_dict = {
        'type': 'Content Modification Time',
        'host': 'ubuntu',
        'filename': 'log/syslog.1',
        'source': 'LOG',
        'description': '[',
        'datetime': '2012-06-27 18:17:01',
        'inreport': '',
        'source_name': '-',
        'extra': (
            'my_number: 123  some_additional_foo: True  text: '
            'Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
            'session closed for user root) '
        ),
        'tag': '',
        'timezone': 'UTC',
        'inode': '-',
        'reportnotes': '',
        'sourcetype': 'Log File',
        'event_identifier': '-',
        'format': '-',
        'URL': '-',
        'record_number': 0,
        'MACB': 'M...',
        'computer_name': '-',
        'offset': 0,
        'evidence': '-',
        'user_sid': '-',
        'notes': '-',
        'vss_store_number': -1,
        'user': '-'
    }

    timestamp = timelib.Timestamp.CopyFromString(
        '2012-06-27 18:17:01+00:00')
    event = MySQL4n6TimeTestEvent(timestamp)
    event_dict = output_module._GetSanitizedEventValues(event)

    self.assertIsInstance(event_dict, dict)
    self.assertDictContainsSubset(expected_dict, event_dict)

  def testSetCredentials(self):
    """Tests the SetCredentials function."""
    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)

    output_module.SetCredentials(password='password', username='username')
    self.assertEqual(output_module._password, 'password')
    self.assertEqual(output_module._user, 'username')

  def testSetDatabaseName(self):
    """Tests the SetDatabaseName function."""
    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)

    output_module.SetDatabaseName('database')
    self.assertEqual(output_module._dbname, 'database')

  def testSetServerInformation(self):
    """Tests the SetServerInformation function."""
    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)

    output_module.SetServerInformation('127.0.0.1', 3306)
    self.assertEqual(output_module._host, '127.0.0.1')
    self.assertEqual(output_module._port, 3306)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    fake_cursor = fake_mysqldb.FakeMySQLdbCursor()
    fake_cursor.expected_query = (
        mysql_4n6time.MySQL4n6TimeOutputModule._INSERT_QUERY)

    fake_cursor.expected_query_args = {
        'computer_name': '-',
        'datetime': '2012-06-27 18:17:01',
        'description': '[',
        'event_identifier': '-',
        'event_type': '-',
        'evidence': '-',
        'extra': (
            'my_number: 123  '
            'some_additional_foo: True  '
            'text: Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
            'session closed for user root) '),
        'filename': 'log/syslog.1',
        'format': '-',
        'host': 'ubuntu',
        'inode': '-',
        'inreport': '',
        'MACB': 'M...',
        'notes': '-',
        'offset': 0,
        'record_number': 0,
        'reportnotes': '',
        'source_name': '-',
        'sourcetype': 'Log File',
        'source': 'LOG',
        'tag': '',
        'timezone': 'UTC',
        'type': 'Content Modification Time',
        'URL': '-',
        'user_sid': '-',
        'user': '-',
        'vss_store_number': -1}

    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)
    output_module._count = 0
    output_module._cursor = fake_cursor

    timestamp = timelib.Timestamp.CopyFromString(
        '2012-06-27 18:17:01+00:00')
    event = MySQL4n6TimeTestEvent(timestamp)
    output_module.WriteEventBody(event)


if __name__ == '__main__':
  unittest.main()
