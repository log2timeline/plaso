#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the 4n6time SQLite output module."""

import os
import unittest

try:
  from pysqlite2 import dbapi2 as sqlite3
except ImportError:
  import sqlite3

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import sqlite_4n6time

from tests import test_lib as shared_test_lib
from tests.output import test_lib


class TestEventData(events.EventData):
  """Event data for testing 4n6time SQLite output module."""

  DATA_TYPE = u'syslog:line'

  def __init__(self):
    """Initializes event data."""
    super(TestEventData, self).__init__(data_type=self.DATA_TYPE)
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.display_name = u'log/syslog.1'
    self.some_additional_foo = True
    self.my_number = 123
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        u'closed for user root)')


class SqliteOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the 4n6time SQLite output module."""

  # TODO: remove after event data refactor.
  def _MergeEventAndEventData(self, event, event_data):
    """Merges the event data with the event.

    args:
      event (EventObject): event.
      event_data (EventData): event_data.
    """
    for attribute_name, attribute_value in event_data.GetAttributes():
      setattr(event, attribute_name, attribute_value)

  def testOutput(self):
    """Tests the 4n6time SQLite output module."""
    event_data = TestEventData()

    timestamp = timelib.Timestamp.CopyFromString(
        u'2012-06-27 18:17:01+00:00')
    event = time_events.TimestampEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)

    self._MergeEventAndEventData(event, event_data)

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
      sqlite_output.WriteEventBody(event)
      sqlite_output.Close()

      sqlite_connection = sqlite3.connect(sqlite_file)
      sqlite_connection.row_factory = sqlite3.Row

      cursor = sqlite_connection.execute(u'SELECT * from log2timeline')
      row = cursor.fetchone()
      row_dict = dict(zip(row.keys(), row))
      self.assertDictContainsSubset(expected_dict, row_dict)


if __name__ == '__main__':
  unittest.main()
