# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android WebviewCache database files."""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidWebViewCacheEventData(events.EventData):
  """Android WebViewCache event data.

  Attributes:
    content_length (int): size of the cached content.
    expiration_time (dfdatetime.DateTimeValues): date and time the cache
        entry expires.
    last_modified_time (dfdatetime.DateTimeValues): date and time the cache
        entry was last modified.
    query (str): SQL query that was used to obtain the event data.
    url (str): URL the content was retrieved from.
  """

  DATA_TYPE = 'android:webviewcache'

  def __init__(self):
    """Initializes event data."""
    super(AndroidWebViewCacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.content_length = None
    self.expiration_time = None
    self.last_modified_time = None
    self.query = None
    self.url = None


class AndroidWebViewCachePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Android WebviewCache database files."""

  NAME = 'android_webviewcache'
  DATA_FORMAT = 'Android WebViewCache SQLite database file'

  REQUIRED_STRUCTURE = {
      'android_metadata': frozenset([]),
      'cache': frozenset(['url', 'contentlength', 'expires', 'lastmodify'])}

  QUERIES = frozenset([
      ('SELECT url, contentlength, expires, lastmodify FROM cache',
       'ParseRow')])

  SCHEMAS = [{
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT)'),
      'cache': (
          'CREATE TABLE cache (_id INTEGER PRIMARY KEY, url TEXT, filepath '
          'TEXT, lastmodify TEXT, etag TEXT, expires INTEGER, expiresstring '
          'TEXT, mimetype TEXT, encoding TEXT, httpstatus INTEGER, location '
          'TEXT, contentlength INTEGER, contentdisposition TEXT, UNIQUE (url) '
          'ON CONFLICT REPLACE)')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.JavaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_java_time.JavaTime(timestamp=timestamp)

  def ParseRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = AndroidWebViewCacheEventData()
    event_data.content_length = self._GetRowValue(
        query_hash, row, 'contentlength')
    event_data.expiration_time = self._GetDateTimeRowValue(
        query_hash, row, 'expires')
    event_data.last_modified_time = self._GetDateTimeRowValue(
        query_hash, row, 'lastmodify')
    event_data.query = query
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidWebViewCachePlugin)
