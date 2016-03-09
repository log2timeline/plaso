# -*- coding: utf-8 -*-
"""This file contains a parser for the Mac OS X application usage.

   The application usage is stored in SQLite database files named
   /var/db/application_usage.sqlite
"""

from plaso.containers import time_events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacOSXApplicationUsageEvent(time_events.PosixTimeEvent):
  """Convenience class for a Mac OS X application usage event."""

  DATA_TYPE = u'macosx:application_usage'

  def __init__(
      self, posix_time, usage, application_name, application_version,
      bundle_id, number_of_times):
    """Initializes the event object.

    Args:
      posix_time: The POSIX time value.
      usage: The description of the usage of the time value.
      application_name: The name of the application.
      application_version: The version of the application.
      bundle_id: The bundle identifier of the application.
      number_of_times: TODO: number of times what?
    """
    super(MacOSXApplicationUsageEvent, self).__init__(posix_time, usage)

    self.application = application_name
    self.app_version = application_version
    self.bundle_id = bundle_id
    self.count = number_of_times


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

  def ParseApplicationUsageRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses an application usage row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    # TODO: replace usage by definition(s) in eventdata. Not sure which values
    # it will hold here.
    usage = u'Application {0:s}'.format(row['event'])

    event_object = MacOSXApplicationUsageEvent(
        row['last_time'], usage, row['app_path'], row['app_version'],
        row['bundle_id'], row['number_times'])
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(ApplicationUsagePlugin)
