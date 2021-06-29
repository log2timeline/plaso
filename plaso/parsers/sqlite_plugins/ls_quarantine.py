# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS LS quarantine events database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


# TODO: describe more clearly what the data value contains.
class LsQuarantineEventData(events.EventData):
  """MacOS launch services quarantine event data.

  Attributes:
    agent (str): user agent that was used to download the file.
    data (bytes): data.
    query (str): SQL query that was used to obtain the event data.
    url (str): original URL of the file.
  """

  DATA_TYPE = 'macosx:lsquarantine'

  def __init__(self):
    """Initializes event data."""
    super(LsQuarantineEventData, self).__init__(data_type=self.DATA_TYPE)
    self.agent = None
    self.data = None
    self.query = None
    self.url = None


class LsQuarantinePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS LS quarantine events database files.

  The MacOS launch services (LS) quarantine database file is typically stored
  in: /Users/<username>/Library/Preferences/
      QuarantineEvents.com.apple.LaunchServices
  """

  NAME = 'ls_quarantine'
  DATA_FORMAT = (
      'MacOS launch services quarantine events database SQLite database file')

  REQUIRED_STRUCTURE = {
      'LSQuarantineEvent': frozenset([
          'LSQuarantineTimeStamp', 'LSQuarantineAgentName',
          'LSQuarantineOriginURLString', 'LSQuarantineDataURLString'])}

  QUERIES = [
      (('SELECT LSQuarantineTimeStamp AS Time, LSQuarantineAgentName AS Agent, '
        'LSQuarantineOriginURLString AS URL, LSQuarantineDataURLString AS Data '
        'FROM LSQuarantineEvent ORDER BY Time'), 'ParseLSQuarantineRow')]

  SCHEMAS = [{
      'LSQuarantineEvent': (
          'CREATE TABLE LSQuarantineEvent ( LSQuarantineEventIdentifier TEXT '
          'PRIMARY KEY NOT NULL, LSQuarantineTimeStamp REAL, '
          'LSQuarantineAgentBundleIdentifier TEXT, LSQuarantineAgentName '
          'TEXT, LSQuarantineDataURLString TEXT, LSQuarantineSenderName TEXT, '
          'LSQuarantineSenderAddress TEXT, LSQuarantineTypeNumber INTEGER, '
          'LSQuarantineOriginTitle TEXT, LSQuarantineOriginURLString TEXT, '
          'LSQuarantineOriginAlias BLOB )')}]

  def ParseLSQuarantineRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a launch services quarantine event row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = LsQuarantineEventData()
    event_data.agent = self._GetRowValue(query_hash, row, 'Agent')
    event_data.data = self._GetRowValue(query_hash, row, 'Data')
    event_data.query = query
    event_data.url = self._GetRowValue(query_hash, row, 'URL')

    timestamp = self._GetRowValue(query_hash, row, 'Time')
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(LsQuarantinePlugin)
