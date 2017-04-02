# -*- coding: utf-8 -*-
"""Plugin for the Mac OS X launch services quarantine events."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


# TODO: describe more clearly what the data value contains.
class LsQuarantineEventData(events.EventData):
  """Mac OS X launch services quarantine event data.

  Attributes:
    data (bytes): data.
    url (str): original URL of the file.
    user_agent (str): user agent that was used to download the file.
  """

  DATA_TYPE = u'macosx:lsquarantine'

  def __init__(self):
    """Initializes event data."""
    super(LsQuarantineEventData, self).__init__(data_type=self.DATA_TYPE)
    self.agent = None
    self.data = None
    self.url = None


class LsQuarantinePlugin(interface.SQLitePlugin):
  """Parses the launch services quarantine events database.

  The LS quarantine events are stored in SQLite database files named
  /Users/<username>/Library/Preferences/
       QuarantineEvents.com.apple.LaunchServices
  """

  NAME = u'ls_quarantine'
  DESCRIPTION = u'Parser for LS quarantine events SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT LSQuarantineTimestamp AS Time, LSQuarantine'
        u'AgentName AS Agent, LSQuarantineOriginURLString AS URL, '
        u'LSQuarantineDataURLString AS Data FROM LSQuarantineEvent '
        u'ORDER BY Time'), u'ParseLSQuarantineRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([u'LSQuarantineEvent'])

  SCHEMAS = [{
      u'LSQuarantineEvent': (
          u'CREATE TABLE LSQuarantineEvent ( LSQuarantineEventIdentifier TEXT '
          u'PRIMARY KEY NOT NULL, LSQuarantineTimeStamp REAL, '
          u'LSQuarantineAgentBundleIdentifier TEXT, LSQuarantineAgentName '
          u'TEXT, LSQuarantineDataURLString TEXT, LSQuarantineSenderName TEXT, '
          u'LSQuarantineSenderAddress TEXT, LSQuarantineTypeNumber INTEGER, '
          u'LSQuarantineOriginTitle TEXT, LSQuarantineOriginURLString TEXT, '
          u'LSQuarantineOriginAlias BLOB )')}]

  def ParseLSQuarantineRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a launch services quarantine event row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = LsQuarantineEventData()
    event_data.agent = row['Agent']
    event_data.data = row['Data']
    event_data.query = query
    event_data.url = row['URL']

    timestamp = row['Time']
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(LsQuarantinePlugin)
