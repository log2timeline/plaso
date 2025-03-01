# -*- coding: utf-8 -*-
"""SQLite parser plugin for IMO HD chat message database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IMOHDChatMessageEventData(events.EventData):
  """IMO HD chat message event data.

  Attributes:
    alias (str): alias (or name) of the author of the message.
    query (str): SQL query that was used to obtain the event data.
    recorded_time (dfdatetime.DateTimeValues): date and time the chat
        message was recorded.
    status (int): send status.
    text (str): text of the chat message.
  """

  DATA_TYPE = 'ios:imohdchat:message'

  def __init__(self):
    """Initializes event data."""
    super(IMOHDChatMessageEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.alias = None
    self.query = None
    self.recorded_time = None
    self.send_status = None
    self.text = None


class IMOHDChatMessagePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for IMO HD chat message database files."""

  NAME = 'ios_imohdchat_message'
  DATA_FORMAT = (
      'IMO HD chat message SQLite database (IMODb2.sqlite) file')

  REQUIRED_STRUCTURE = {
      'ZIMOCHATMSG': frozenset([
          'Z_PK', 'ZALIAS', 'ZTEXT', 'ZISSENT', 'ZTS'])}

  QUERIES = [(
      'SELECT ZTS, ZALIAS, ZTEXT, ZISSENT FROM ZIMOCHATMSG',
      'ParseApplicationUsageRow')]

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

    return dfdatetime_posix_time.PosixTimeInNanoseconds(timestamp=timestamp)

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

    # TODO: add attribute for ZSENDERTS
    event_data = IMOHDChatMessageEventData()
    event_data.alias = self._GetRowValue(query_hash, row, 'ZALIAS')
    event_data.query = query
    event_data.recorded_time = self._GetDateTimeRowValue(query_hash, row, 'ZTS')
    event_data.status = self._GetRowValue(query_hash, row, 'ZISSENT')
    event_data.text = self._GetRowValue(query_hash, row, 'ZTEXT')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IMOHDChatMessagePlugin)
