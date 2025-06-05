# -*- coding:utf-8 -*-
"""SQLite parser plugin for TikTok contacts database on iOS."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSTikTokContactsEventData(events.EventData):
  """iOS TikTok contacts event data.

  Attributes:
    chat_timestamp (dfdatetime.DateTimeValues): latest chat timestamp.
    nickname (str): nickname of the contact.
    url (str): url of the contact.
  """

  DATA_TYPE = 'ios:tiktok:contact'

  def __init__(self):
    """Initializes event data."""
    super(IOSTikTokContactsEventData, self).__init__(data_type=self.DATA_TYPE)
    self.chat_timestamp = None
    self.nickname = None
    self.url = None


class IOSTikTokContactsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for TikTok contacts database on iOS.

  The TikTok contacts are stored in a SQLite database file named AwemeIM.db.
  """

  NAME = 'ios_tiktok_contacts'
  DATA_FORMAT = 'iOS TikTok contacts SQLite database file AwemeIM.db'

  REQUIRED_STRUCTURE = {
    'AwemeContactsV5': frozenset([
        'latestChatTimestamp', 'nickname', 'url1'])}

  QUERIES = [((
      'SELECT latestChatTimestamp, nickname, url1 FROM AwemeContactsV5'),
      'ParseContactRow')]

  SCHEMAS = {
    'AwemeContactsV5': (
        'CREATE TABLE AwemeContactsV5 (uid TEXT PRIMARY KEY, '
        'accountType INTEGER, alias TEXT, aliasPinYin TEXT, '
        'commerceUserLevel BLOB, contactName TEXT, contactNamePinYin TEXT, '
        'customID TEXT, customVerifyInfo TEXT, enterpriseVerifyInfo TEXT, '
        'followStatus INTEGER, followerCount BLOB, followingCount BLOB, '
        'hasSetWelcomeMessage INTEGER, latestChatTimestamp INTEGER, '
        'mentionAccessModel BLOB, nickname TEXT, nicknamePinYin TEXT, '
        'recType INTEGER, secUserID TEXT, shortID TEXT, signature TEXT, '
        'updatedTriggeredByContactModule INTEGER, url1 TEXT, url2 TEXT, '
        'url3 TEXT, verificationType INTEGER)')}

  REQUIRE_SCHEMA_MATCH = False

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

    # Convert the floating point value to an integer.
    timestamp = int(timestamp)
    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  # pylint: disable=unused-argument
  def ParseContactRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a contact row.

    Args:
    parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfVFS.
    query (str): query that created the row.
    row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IOSTikTokContactsEventData()
    event_data.chat_timestamp = self._GetDateTimeRowValue(
        query_hash, row, 'latestChatTimestamp')
    event_data.nickname = self._GetRowValue(query_hash, row, 'nickname')
    event_data.url = self._GetRowValue(query_hash, row, 'url1')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSTikTokContactsPlugin)
