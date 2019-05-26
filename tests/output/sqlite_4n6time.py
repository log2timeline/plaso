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

from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import sqlite_4n6time

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class SqliteOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the 4n6time SQLite output module."""

  _TEST_EVENTS = [
      {'data_type': 'syslog:line',
       'display_name': 'log/syslog.1',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'my_number': 123,
       'some_additional_foo': True,
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString(
           '2012-06-27 18:17:01+00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}]

  def testOutput(self):
    """Tests the 4n6time SQLite output module."""
    with shared_test_lib.TempDirectory() as temp_directory:
      output_mediator = self._CreateOutputMediator()
      sqlite_output = sqlite_4n6time.SQLite4n6TimeOutputModule(
          output_mediator)

      sqlite_file = os.path.join(temp_directory, '4n6time.db')
      sqlite_output.SetFilename(sqlite_file)

      sqlite_output.Open()

      event, event_data = containers_test_lib.CreateEventFromValues(
          self._TEST_EVENTS[0])
      sqlite_output.WriteEventBody(event, event_data, None)

      sqlite_output.Close()

      sqlite_connection = sqlite3.connect(sqlite_file)
      sqlite_connection.row_factory = sqlite3.Row

      cursor = sqlite_connection.execute('SELECT * from log2timeline')
      row = cursor.fetchone()
      row_dict = dict(zip(row.keys(), row))

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
        'user': '-'}

    self.assertDictContainsSubset(expected_dict, row_dict)


if __name__ == '__main__':
  unittest.main()
