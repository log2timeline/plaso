#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the 4n6time MySQL output class."""

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

  DATA_TYPE = u'syslog:line'

  def __init__(self, event_timestamp):
    """Initializes an event."""
    super(MySQL4n6TimeTestEvent, self).__init__()
    self.display_name = u'log/syslog.1'
    self.filename = u'log/syslog.1'
    self.hostname = u'ubuntu'
    self.my_number = 123
    self.some_additional_foo = True
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        u'closed for user root)')
    self.timestamp_desc = definitions.TIME_DESCRIPTION_WRITTEN
    self.timestamp = event_timestamp


class MySQL4n6TimeOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the 4n6time MySQL output class."""

  # pylint: disable=protected-access

  def testGetTags(self):
    """Tests the _GetTags function."""
    fake_cursor = fake_mysqldb.FakeMySQLdbCursor()
    fake_cursor.expected_query = u'SELECT DISTINCT tag FROM log2timeline'
    fake_cursor.query_results = [(u'one',), (u'two,three',), (u'four',)]

    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)
    output_module._cursor = fake_cursor

    expected_tags = [u'one', u'two', u'three', u'four']
    tags = output_module._GetTags()
    self.assertEqual(tags, expected_tags)

  def testGetUniqueValues(self):
    """Tests the _GetUniqueValues function."""
    fake_cursor = fake_mysqldb.FakeMySQLdbCursor()
    fake_cursor.expected_query = (
        u'SELECT source, COUNT(source) FROM log2timeline GROUP BY source')
    fake_cursor.query_results = [(u'one', 1), (u'two', 2), (u'three', 3)]

    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)
    output_module._cursor = fake_cursor

    expected_unique_values = {u'one': 1, u'two': 2, u'three': 3}
    unique_values = output_module._GetUniqueValues(u'source')
    self.assertEqual(unique_values, expected_unique_values)

  # TODO: add test for Open and Close

  def testGetSanitizedEventValues(self):
    """Tests the GetSanitizedEventValues function."""
    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)

    expected_dict = {
        u'type': u'Content Modification Time',
        u'host': u'ubuntu',
        u'filename': u'log/syslog.1',
        u'source': u'LOG',
        u'description': u'[',
        u'datetime': u'2012-06-27 18:17:01',
        u'inreport': u'',
        u'source_name': u'-',
        u'extra': (
            u'my_number: 123  some_additional_foo: True  text: '
            u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
            u'session closed for user root) '
        ),
        u'tag': u'',
        u'timezone': u'UTC',
        u'inode': u'-',
        u'reportnotes': u'',
        u'sourcetype': u'Log File',
        u'event_identifier': u'-',
        u'format': u'-',
        u'URL': u'-',
        u'record_number': 0,
        u'MACB': u'M...',
        u'computer_name': u'-',
        u'offset': 0,
        u'evidence': u'-',
        u'user_sid': u'-',
        u'notes': u'-',
        u'vss_store_number': -1,
        u'user': u'-'
    }

    timestamp = timelib.Timestamp.CopyFromString(
        u'2012-06-27 18:17:01+00:00')
    event = MySQL4n6TimeTestEvent(timestamp)
    event_dict = output_module._GetSanitizedEventValues(event)

    self.assertIsInstance(event_dict, dict)
    self.assertDictContainsSubset(expected_dict, event_dict)

  def testSetCredentials(self):
    """Tests the SetCredentials function."""
    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)

    output_module.SetCredentials(password=u'password', username=u'username')
    self.assertEqual(output_module._password, u'password')
    self.assertEqual(output_module._user, u'username')

  def testSetDatabaseName(self):
    """Tests the SetDatabaseName function."""
    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)

    output_module.SetDatabaseName(u'database')
    self.assertEqual(output_module._dbname, u'database')

  def testSetServerInformation(self):
    """Tests the SetServerInformation function."""
    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)

    output_module.SetServerInformation(u'127.0.0.1', 3306)
    self.assertEqual(output_module._host, u'127.0.0.1')
    self.assertEqual(output_module._port, 3306)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""
    fake_cursor = fake_mysqldb.FakeMySQLdbCursor()
    fake_cursor.expected_query = (
        mysql_4n6time.MySQL4n6TimeOutputModule._INSERT_QUERY)

    fake_cursor.expected_query_args = {
        u'computer_name': u'-',
        u'datetime': u'2012-06-27 18:17:01',
        u'description': u'[',
        u'event_identifier': u'-',
        u'event_type': u'-',
        u'evidence': u'-',
        u'extra': (
            u'my_number: 123  '
            u'some_additional_foo: True  '
            u'text: Reporter <CRON> PID: 8442 (pam_unix(cron:session): '
            u'session closed for user root) '),
        u'filename': u'log/syslog.1',
        u'format': u'-',
        u'host': u'ubuntu',
        u'inode': u'-',
        u'inreport': u'',
        u'MACB': u'M...',
        u'notes': u'-',
        u'offset': 0,
        u'record_number': 0,
        u'reportnotes': u'',
        u'source_name': u'-',
        u'sourcetype': u'Log File',
        u'source': u'LOG',
        u'tag': u'',
        u'timezone': u'UTC',
        u'type': u'Content Modification Time',
        u'URL': u'-',
        u'user_sid': u'-',
        u'user': u'-',
        u'vss_store_number': -1}

    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)
    output_module._count = 0
    output_module._cursor = fake_cursor

    timestamp = timelib.Timestamp.CopyFromString(
        u'2012-06-27 18:17:01+00:00')
    event = MySQL4n6TimeTestEvent(timestamp)
    output_module.WriteEventBody(event)


if __name__ == '__main__':
  unittest.main()
