# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS application usage database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacOSApplicationUsageEventData(events.EventData):
  """MacOS application usage event data.

  Attributes:
    application (str): name of the application.
    application_version (str): version of the application.
    bundle_identifier (str): bundle identifier of the application.
    count (int): number of occurances of the event.
    event (str): event.
    last_used_time (dfdatetime.DateTimeValues): last date and time
        the application was last used.
    query (str): SQL query that was used to obtain the event data.
  """

  DATA_TYPE = 'macos:application_usage:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSApplicationUsageEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application = None
    self.application_version = None
    self.bundle_identifier = None
    self.count = None
    self.event = None
    self.last_used_time = None
    self.query = None


class MacOSApplicationUsagePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS application usage database files.

  The MacOS application usage database is typically stored in:
  /var/db/application_usage.sqlite

  Application usage is a SQLite database that logs down entries triggered by
  NSWorkspaceWillLaunchApplicationNotification and
  NSWorkspaceDidTerminateApplicationNotification NSWorkspace notifications by
  crankd.

  More information can be found here:
  https://github.com/google/macops/blob/master/crankd/ApplicationUsage.py
  """

  NAME = 'appusage'
  DATA_FORMAT = (
      'MacOS application usage SQLite database (application_usage.sqlite) file')

  REQUIRED_STRUCTURE = {
      'application_usage': frozenset([
          'last_time', 'event', 'bundle_id', 'app_version', 'app_path',
          'number_times'])}

  QUERIES = [(
      ('SELECT last_time, event, bundle_id, app_version, app_path, '
       'number_times FROM application_usage ORDER BY last_time'),
      'ParseApplicationUsageRow')]

  SCHEMAS = [{
      'application_usage': (
          'CREATE TABLE application_usage (event TEXT, bundle_id TEXT, '
          'app_version TEXT, app_path TEXT, last_time INTEGER DEFAULT 0, '
          'number_times INTEGER DEFAULT 0, PRIMARY KEY (event, bundle_id))')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def ParseApplicationUsageRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses an application usage row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = MacOSApplicationUsageEventData()
    event_data.application = self._GetRowValue(query_hash, row, 'app_path')
    event_data.application_version = self._GetRowValue(
        query_hash, row, 'app_version')
    event_data.bundle_identifier = self._GetRowValue(
        query_hash, row, 'bundle_id')
    event_data.count = self._GetRowValue(query_hash, row, 'number_times')
    event_data.event = self._GetRowValue(query_hash, row, 'event')
    event_data.last_used_time = self._GetDateTimeRowValue(
        query_hash, row, 'last_time')
    event_data.query = query

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(MacOSApplicationUsagePlugin)
