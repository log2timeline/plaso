# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS and iOS iMessage database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time
from dfdatetime import definitions as dfdatetime_definitions

from plaso.containers import events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IMessageEventData(events.EventData):
  """iMessage and SMS event data.

  Attributes:
    attachment_location (str): location of the attachment.
    client_version (int): client version.
    creation_time (dfdatetime.DateTimeValues): date and time the message
        was created.
    imessage_id (str): mobile number or email address the message was sent
        to or received from.
    message_type (int): value to indicate the message was sent (1) or
        received (0).
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    read_receipt (bool): True if the message read receipt was received.
    service (str): service, which is either SMS or iMessage.
    text (str): content of the message.
  """

  DATA_TYPE = 'imessage:event:chat'

  def __init__(self):
    """Initializes event data."""
    super(IMessageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.attachment_location = None
    self.client_version = None
    self.creation_time = None
    self.imessage_id = None
    self.message_type = None
    self.offset = None
    self.query = None
    self.read_receipt = None
    self.service = None
    self.text = None


class IMessagePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS and iOS iMessage database files.

  The iMessage database file is typically stored in chat.db or sms.db.
  """

  NAME = 'imessage'
  DATA_FORMAT = 'MacOS and iOS iMessage database (chat.db, sms.db) file'

  REQUIRED_STRUCTURE = {
      '_SqliteDatabaseProperties': frozenset([
          'key', 'value']),
      'message': frozenset([
          'date', 'ROWID', 'is_read', 'is_from_me', 'service', 'text',
          'handle_id']),
      'handle': frozenset([
          'id', 'ROWID']),
      'attachment': frozenset([
          'filename', 'ROWID']),
      'message_attachment_join': frozenset([
          'message_id', 'attachment_id'])}

  QUERIES = [
      ('SELECT message.date, message.ROWID, handle.id AS imessage_id, '
       'message.is_read AS read_receipt, message.is_from_me AS message_type, '
       'message.service, attachment.filename AS attachment_location, '
       'message.text FROM message JOIN handle '
       'ON handle.ROWID = message.handle_id '
       'LEFT OUTER JOIN message_attachment_join AS maj '
       'ON message.ROWID = maj.message_id LEFT OUTER JOIN attachment '
       'ON maj.attachment_id = attachment.ROWID', 'ParseMessageRow')]

  _CLIENT_VERSION_QUERY = (
      'SELECT key, value FROM _SqliteDatabaseProperties '
      'WHERE key = "_ClientVersion"')

  def _GetClientVersion(self, cache, database):
    """Retrieves the client version.

    Args:
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.

    Returns:
      int: client version or None if the client version cannot be determined.
    """
    cache_results = cache.GetResults('client_version')
    if not cache_results:
      query_result = database.Query(self._CLIENT_VERSION_QUERY)

      cache.CacheQueryResults(
          query_result, 'client_version', 'key', ('value', ))
      cache_results = cache.GetResults('client_version')

    client_version = cache_results.get('_ClientVersion', [])[0]

    if isinstance(client_version, str):
      try:
        client_version = int(client_version, 10)
        cache_results['_ClientVersion'] = [client_version]
      except (ValueError, TypeError):
        return None

    return client_version

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

    precision = dfdatetime_definitions.PRECISION_1_SECOND

    # In current versions the timestamp is stored in nanoseconds.
    # Note that a Cocoa timestamp of 1000000000 is somewhere in 2032 and
    # the timestamp apprears to have been changes around 2017.
    if (timestamp < -definitions.NANOSECONDS_PER_SECOND or
        timestamp > definitions.NANOSECONDS_PER_SECOND):
      timestamp /= definitions.NANOSECONDS_PER_SECOND
      precision = dfdatetime_definitions.PRECISION_1_NANOSECOND

    return dfdatetime_cocoa_time.CocoaTime(
        precision=precision, timestamp=timestamp)

  def ParseMessageRow(
      self, parser_mediator, query, row, cache=None, database=None,
      **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
      cache (SQLiteCache): cache which contains cached results from querying
          the visits and urls tables.
      database (Optional[SQLiteDatabase]): database.
    """
    query_hash = hash(query)

    event_data = IMessageEventData()
    event_data.attachment_location = self._GetRowValue(
        query_hash, row, 'attachment_location')
    event_data.client_version = self._GetClientVersion(cache, database)
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'date')
    event_data.imessage_id = self._GetRowValue(query_hash, row, 'imessage_id')
    event_data.message_type = self._GetRowValue(query_hash, row, 'message_type')
    event_data.offset = self._GetRowValue(query_hash, row, 'ROWID')
    event_data.query = query
    event_data.read_receipt = self._GetRowValue(query_hash, row, 'read_receipt')
    event_data.service = self._GetRowValue(query_hash, row, 'service')
    event_data.text = self._GetRowValue(query_hash, row, 'text')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IMessagePlugin)
