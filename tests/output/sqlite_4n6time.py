#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the 4n6time SQLite output module."""

from __future__ import unicode_literals

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

  DATA_TYPE = 'syslog:line'

  def __init__(self):
    """Initializes event data."""
    super(TestEventData, self).__init__(data_type=self.DATA_TYPE)
    self.hostname = 'ubuntu'
    self.filename = 'log/syslog.1'
    self.display_name = 'log/syslog.1'
    self.some_additional_foo = True
    self.my_number = 123
    self.text = (
        'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        'closed for user root)')


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
        '2012-06-27 18:17:01+00:00')
    event = time_events.TimestampEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)

    self._MergeEventAndEventData(event, event_data)

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
            'session closed for user root) '),
        'tag': '',
        'timezone': 'UTC',
        'inode': '-',
        'reportnotes': '',
        'sourcetype': 'Log File',
        'event_identifier': '-',
        'format': '-',
        'url': '-',
        'record_number': '0',
        'MACB': 'M...',
        'computer_name': '-',
        'offset': 0,
        'evidence': '-',
        'user_sid': '-',
        'notes': '-',
        'vss_store_number': -1,
        'user': '-'
    }
    with shared_test_lib.TempDirectory() as temp_directory:
      output_mediator = self._CreateOutputMediator()
      sqlite_output = sqlite_4n6time.SQLite4n6TimeOutputModule(
          output_mediator)

      sqlite_file = os.path.join(temp_directory, '4n6time.db')
      sqlite_output.SetFilename(sqlite_file)

      sqlite_output.Open()
      sqlite_output.WriteEventBody(event)
      sqlite_output.Close()

      sqlite_connection = sqlite3.connect(sqlite_file)
      sqlite_connection.row_factory = sqlite3.Row

      cursor = sqlite_connection.execute('SELECT * from log2timeline')
      row = cursor.fetchone()
      row_dict = dict(zip(row.keys(), row))
      self.assertDictContainsSubset(expected_dict, row_dict)


if __name__ == '__main__':
  unittest.main()
