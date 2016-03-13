#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the 4n6time SQLite output class."""

import os
import unittest

try:
  from pysqlite2 import dbapi2 as sqlite3
except ImportError:
  import sqlite3

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import sqlite_4n6time

from tests import test_lib as shared_test_lib
from tests.output import test_lib


class SQLiteTestEvent(time_events.TimestampEvent):
  """Event object used for testing."""

  DATA_TYPE = u'syslog:line'

  def __init__(self, timestamp):
    """Initializes an event object.

    Args:
      timestamp: the timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
    """
    super(SQLiteTestEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME)
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.display_name = u'log/syslog.1'
    self.some_additional_foo = True
    self.my_number = 123
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        u'closed for user root)')


class SqliteOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the sqlite output class."""

  def testOutput(self):
    """Tests for the sqlite output."""
    timestamp = timelib.Timestamp.CopyFromString(
        u'2012-06-27 18:17:01+00:00')
    event_object = SQLiteTestEvent(timestamp)

    # pylint: disable=missing-docstring
    def dict_from_row(row):
      return dict(zip(row.keys(), row))

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
            u'session closed for user root) '),
        u'tag': u'',
        u'timezone': u'UTC',
        u'inode': u'-',
        u'reportnotes': u'',
        u'sourcetype': u'Log File',
        u'event_identifier': u'-',
        u'format': u'-',
        u'url': u'-',
        u'record_number': u'0',
        u'MACB': u'M...',
        u'computer_name': u'-',
        u'offset': 0,
        u'evidence': u'-',
        u'user_sid': u'-',
        u'notes': u'-',
        u'vss_store_number': -1,
        u'user': u'-'
    }
    with shared_test_lib.TempDirectory() as temp_directory:
      output_mediator = self._CreateOutputMediator()
      sqlite_output = sqlite_4n6time.SQLite4n6TimeOutputModule(
          output_mediator)

      sqlite_file = os.path.join(temp_directory, u'4n6time.db')
      sqlite_output.SetFilename(sqlite_file)

      sqlite_output.Open()
      sqlite_output.WriteEventBody(event_object)
      sqlite_output.Close()

      sqlite_connection = sqlite3.connect(sqlite_file)
      sqlite_connection.row_factory = sqlite3.Row

      res = sqlite_connection.execute(u'SELECT * from log2timeline')
      row_dict = dict_from_row(res.fetchone())
      self.assertDictContainsSubset(expected_dict, row_dict)


if __name__ == '__main__':
  unittest.main()
