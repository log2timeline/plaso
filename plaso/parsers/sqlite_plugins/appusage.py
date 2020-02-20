# -*- coding: utf-8 -*-
"""This file contains a parser for the MacOS application usage.

The application usage is stored in SQLite database files named
/var/db/application_usage.sqlite
"""

from __future__ import unicode_literals

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

  NAME = 'appusage'
  DESCRIPTION = 'Parser for MacOS application usage SQLite database files.'

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
