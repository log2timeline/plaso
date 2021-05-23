# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android WebviewCache database files."""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidWebViewCacheEventData(events.EventData):
  """Android WebViewCache event data.

  Attributes:
    content_length (int): size of the cached content.
    query (str): SQL query that was used to obtain the event data.
    url (str): URL the content was retrieved from.
  """

  DATA_TYPE = 'android:webviewcache'

  def __init__(self):
    """Initializes event data."""
    super(AndroidWebViewCacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.content_length = None
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

  def ParseRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = AndroidWebViewCacheEventData()
    event_data.content_length = self._GetRowValue(
        query_hash, row, 'contentlength')
    event_data.query = query
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    timestamp = self._GetRowValue(query_hash, row, 'expires')
    if timestamp is not None:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'lastmodify')
    if timestamp is not None:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidWebViewCachePlugin)
