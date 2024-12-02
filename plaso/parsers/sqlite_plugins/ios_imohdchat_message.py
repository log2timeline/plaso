# -*- coding: utf-8 -*-
"""SQLite parser plugin for IMO HD chat message database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface

class IMOHDChatMessageEventData(events.EventData):
  """IMO HD chat message event data.

  Attributes:
    application (str): name of the application.
    bundle_identifier (str): bundle identifier of the application.
    count (int): number of occurances of the event.
    event (str): event.
    last_used_time (dfdatetime.DateTimeValues): last date and time
        the application was last used.
    query (str): SQL query that was used to obtain the event data.
  """

  DATA_TYPE = 'ios:imohdchat_message:entry'

  def __init__(self):
    """Initializes event data."""
    super(IMOHDChatMessageEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.zalias = None
    self.ztext = None
    self.zissent = None
    self.zts = None
    self.query = None


class IMOHDChatMessagePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for IMO HD chat message database files.
  """

  NAME = 'ios_imohdchat_message'
  DATA_FORMAT = (
      'IMO HD chat message SQLite database (IMODb2.sqlite) file')

  REQUIRED_STRUCTURE = {
      'ZIMOCHATMSG': frozenset([
          'Z_PK', 'ZALIAS', 'ZTEXT', 'ZISSENT',
          'ZTS'])}

  QUERIES = [(
      ('SELECT ZTS/1000000000, ZALIAS, ZTEXT, ZISSENT '
       'FROM ZIMOCHATMSG ORDER BY ZTS'),
      'ParseApplicationUsageRow')]

  SCHEMAS = [{
      'application_usage': (
          'CREATE TABLE ZIMOCHATMSG (Z_PK INTEGER, ZALIAS TEXT, ZTEXT TEXT, ZISSENT INTEGER '
          'ZTS INTEGER, '
          'PRIMARY KEY (Z_PK))')}]

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

    event_data = IMOHDChatMessageEventData()
    event_data.zalias = self._GetRowValue(query_hash, row, 'ZALIAS')
    event_data.ztext = self._GetRowValue(query_hash, row, 'ZTEXT')
    event_data.zissent = self._GetRowValue(query_hash, row, 'ZISSENT')
    event_data.zts = self._GetDateTimeRowValue(
        query_hash, row, 'ZTS/1000000000')
    event_data.query = query

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IMOHDChatMessagePlugin)