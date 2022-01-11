# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS application usage database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacOSApplicationUsageEventData(events.EventData):
  """MacOS application usage event data.

  Attributes:
    application (str): name of the application.
    app_version (str): version of the application.
    bundle_id (str): bundle identifier of the application.
    count (int): TODO: number of times what?
    query (str): SQL query that was used to obtain the event data.
  """

  DATA_TYPE = 'macosx:application_usage'

  def __init__(self):
    """Initializes event data."""
    super(MacOSApplicationUsageEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application = None
    self.app_version = None
    self.bundle_id = None
    self.count = None
    self.query = None


class ApplicationUsagePlugin(interface.SQLitePlugin):
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

  def ParseApplicationUsageRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses an application usage row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    # TODO: replace usage by definition(s) in eventdata. Not sure which values
    # it will hold here.
    application_name = self._GetRowValue(query_hash, row, 'event')
    usage = 'Application {0:s}'.format(application_name)

    event_data = MacOSApplicationUsageEventData()
    event_data.application = self._GetRowValue(query_hash, row, 'app_path')
    event_data.app_version = self._GetRowValue(query_hash, row, 'app_version')
    event_data.bundle_id = self._GetRowValue(query_hash, row, 'bundle_id')
    event_data.count = self._GetRowValue(query_hash, row, 'number_times')
    event_data.query = query

    timestamp = self._GetRowValue(query_hash, row, 'last_time')
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(date_time, usage)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ApplicationUsagePlugin)
