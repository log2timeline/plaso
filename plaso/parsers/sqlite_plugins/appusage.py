# -*- coding: utf-8 -*-
"""This file contains a parser for the Mac OS X application usage.

The application usage is stored in SQLite database files named
/var/db/application_usage.sqlite
"""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacOSXApplicationUsageEventData(events.EventData):
  """Mac OS X application usage event data.

  Attributes:
    application (str): name of the application.
    app_version (str): version of the application.
    bundle_id (str): bundle identifier of the application.
    count (int): TODO: number of times what?
  """

  DATA_TYPE = u'macosx:application_usage'

  def __init__(self):
    """Initializes event data."""
    super(MacOSXApplicationUsageEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application = None
    self.app_version = None
    self.bundle_id = None
    self.count = None


class ApplicationUsagePlugin(interface.SQLitePlugin):
  """Parse Application Usage history files.

  Application usage is a SQLite database that logs down entries
  triggered by NSWorkspaceWillLaunchApplicationNotification and
  NSWorkspaceDidTerminateApplicationNotification NSWorkspace notifications by
  crankd.

  See the code here:
  http://code.google.com/p/google-macops/source/browse/trunk/crankd/\
      ApplicationUsage.py

  Default installation: /var/db/application_usage.sqlite
  """

  NAME = u'appusage'
  DESCRIPTION = u'Parser for Mac OS X application usage SQLite database files.'

  # Define the needed queries.
  QUERIES = [(
      (u'SELECT last_time, event, bundle_id, app_version, app_path, '
       u'number_times FROM application_usage ORDER BY last_time'),
      u'ParseApplicationUsageRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([u'application_usage'])

  SCHEMAS = [{
      u'application_usage': (
          u'CREATE TABLE application_usage (event TEXT, bundle_id TEXT, '
          u'app_version TEXT, app_path TEXT, last_time INTEGER DEFAULT 0, '
          u'number_times INTEGER DEFAULT 0, PRIMARY KEY (event, bundle_id))')}]

  def ParseApplicationUsageRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses an application usage row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    # TODO: replace usage by definition(s) in eventdata. Not sure which values
    # it will hold here.
    usage = u'Application {0:s}'.format(row['event'])

    event_data = MacOSXApplicationUsageEventData()
    event_data.application = row['app_path']
    event_data.app_version = row['app_version']
    event_data.bundle_id = row['bundle_id']
    event_data.count = row['number_times']
    event_data.query = query

    date_time = dfdatetime_posix_time.PosixTime(timestamp=row['last_time'])
    event = time_events.DateTimeValuesEvent(date_time, usage)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ApplicationUsagePlugin)
