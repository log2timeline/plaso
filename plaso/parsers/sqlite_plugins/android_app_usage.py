# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android app_usage database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidAppUsage(events.EventData):
  """Android app usage event data.

  Attributes:
    package_name (str): name of the launched package.
    start_time (dfdatetime.DateTimeValues): date and time when the application
        was launched.
  """

  DATA_TYPE = 'android:sqlite:app_usage'

  def __init__(self):
    """Initializes event data."""
    super(AndroidAppUsage, self).__init__(data_type=self.DATA_TYPE)
    self.package_name = None
    self.start_time = None


class AndroidSQLiteAppUsage(interface.SQLitePlugin):
  """SQLite parser plugin for Android application usage database files."""

  NAME = 'android_app_usage'
  DATA_FORMAT = 'Android app_usage SQLite database (app_usage) file'

  REQUIRED_STRUCTURE = {
      'events': frozenset(['_id', 'timestamp', 'package_id']),
      'packages': frozenset(['_id', 'package_name'])
  }

  QUERIES = [
      ('SELECT events.timestamp, packages.package_name FROM events JOIN '
       'packages ON packages._id = events.package_id', 'ParseAppUsageRow')]

  SCHEMAS = [{
      'events': (
          'CREATE TABLE "events" (_id INTEGER PRIMARY KEY,timestamp INTEGER '
          'NOT NULL,type INTEGER NOT NULL,package_id INTEGER NOT NULL '
          'REFERENCES packages(_id) ON UPDATE CASCADE ON DELETE CASCADE, '
          'instance_id INTEGER DEFAULT NULL, task_root_package_id INTEGER '
          'DEFAULT NULL REFERENCES packages(_id) ON UPDATE CASCADE ON DELETE '
          'CASCADE)'),
      'packages': (
          'CREATE TABLE packages (_id INTEGER PRIMARY KEY,package_name TEXT, '
          'UNIQUE(package_name) ON CONFLICT ABORT)')}]

  def ParseAppUsageRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses an event record row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = AndroidAppUsage()
    event_data.package_name = self._GetRowValue(query_hash, row, 'package_name')

    timestamp = self._GetRowValue(query_hash, row, 'timestamp')
    event_data.start_time = dfdatetime_posix_time.PosixTimeInMilliseconds(
        timestamp=timestamp)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidSQLiteAppUsage)
