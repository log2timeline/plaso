# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS LS quarantine events database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


# TODO: describe more clearly what the data value contains.
class MacOSLSQuarantineEventData(events.EventData):
  """MacOS launch services quarantine event data.

  Attributes:
    agent (str): user agent that was used to download the file.
    data (bytes): data.
    downloaded_time (dfdatetime.DateTimeValues): date and time the file
        was downloaded.
    query (str): SQL query that was used to obtain the event data.
    url (str): original URL of the file.
  """

  DATA_TYPE = 'macos:lsquarantine:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLSQuarantineEventData, self).__init__(data_type=self.DATA_TYPE)
    self.agent = None
    self.data = None
    self.downloaded_time = None
    self.query = None
    self.url = None


class MacOSLSQuarantinePlugin(interface.SQLitePlugin):
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

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  def ParseLSQuarantineRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a launch services quarantine event row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = MacOSLSQuarantineEventData()
    event_data.agent = self._GetRowValue(query_hash, row, 'Agent')
    event_data.data = self._GetRowValue(query_hash, row, 'Data')
    event_data.downloaded_time = self._GetDateTimeRowValue(
        query_hash, row, 'Time')
    event_data.query = query
    event_data.url = self._GetRowValue(query_hash, row, 'URL')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(MacOSLSQuarantinePlugin)
