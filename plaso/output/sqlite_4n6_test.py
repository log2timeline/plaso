#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the sqlite output class."""

import os
import shutil
import tempfile
import unittest

import sqlite3

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import test_lib
from plaso.output import sqlite_4n6


class TempDirectory(object):
  """A self cleaning temporary directory."""

  def __init__(self):
    """Initializes the temporary directory."""
    super(TempDirectory, self).__init__()
    self.name = u''

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()
    return self.name

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)


class sqliteTestEvent(event.EventObject):
  """Simplified EventObject for testing."""

  DATA_TYPE = u'syslog:line'

  def __init__(self, event_timestamp):
    """Initialize event with data."""

    super(sqliteTestEvent, self).__init__()

    self.timestamp = event_timestamp
    self.timestamp_desc = eventdata.EventTimestamp.WRITTEN_TIME
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.display_name = u'log/syslog.1'
    self.some_additional_foo = True
    self.my_number = 123
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        u'closed for user root)')
    self.store_number = 1
    self.store_index = 1


class SqliteOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the sqlite output class."""

  def setUp(self):
    """Sets up the objects needed for this test."""

    plaso_timestamp = timelib.Timestamp()
    self._event_timestamp = plaso_timestamp.CopyFromString(
        u'2012-06-27 18:17:01+00:00')
    self._event_object = sqliteTestEvent(self._event_timestamp)


  def testOutput(self):
    """Tests for the sqlite output."""

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
        u'color': u'',
        u'tag': u'',
        u'timezone': u'UTC',
        u'inode': u'-',
        u'reportnotes': u'',
        u'sourcetype': u'Log File',
        u'event_identifier': u'-',
        u'store_number': 1,
        u'format': u'-',
        u'url': u'-',
        u'store_index': 1,
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
    with TempDirectory() as dirname:
      temp_file = os.path.join(dirname, u'sqlite_4n6.out')
      output_mediator = self._CreateOutputMediator(storage_object=temp_file)
      self._sqlite_output = sqlite_4n6.SQLite4n6OutputModule(
          output_mediator, filehandle=temp_file)
      self._sqlite_output.Open()
      self._sqlite_output.WriteEventBody(self._event_object)
      self._sqlite_output.Close()
      self.conn = sqlite3.connect(temp_file)
      self.conn.row_factory = sqlite3.Row
      res = self.conn.execute('select * from log2timeline')
      row_dict = dict_from_row(res.fetchone())
      self.assertDictContainsSubset(expected_dict, row_dict)


if __name__ == '__main__':
  unittest.main()
