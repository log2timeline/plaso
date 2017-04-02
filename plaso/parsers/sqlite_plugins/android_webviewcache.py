# -*- coding: utf-8 -*-
"""Parser for Android WebviewCache databases."""

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
    url (str): URL the content was retrieved from.
  """

  DATA_TYPE = u'android:webviewcache'

  def __init__(self):
    """Initializes event data."""
    super(AndroidWebViewCacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.content_length = None
    self.url = None


class AndroidWebViewCachePlugin(interface.SQLitePlugin):
  """Parser for Android WebViewCache databases."""

  NAME = u'android_webviewcache'
  DESCRIPTION = u'Parser for Android WebViewCache databases'

  REQUIRED_TABLES = frozenset([u'android_metadata', u'cache'])

  QUERIES = frozenset([
      (u'SELECT url, contentlength, expires, lastmodify FROM cache',
       u'ParseRow')])

  SCHEMAS = [{
      u'android_metadata': (
          u'CREATE TABLE android_metadata (locale TEXT)'),
      u'cache': (
          u'CREATE TABLE cache (_id INTEGER PRIMARY KEY, url TEXT, filepath '
          u'TEXT, lastmodify TEXT, etag TEXT, expires INTEGER, expiresstring '
          u'TEXT, mimetype TEXT, encoding TEXT, httpstatus INTEGER, location '
          u'TEXT, contentlength INTEGER, contentdisposition TEXT, UNIQUE (url) '
          u'ON CONFLICT REPLACE)')}]

  def ParseRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string']
    # and will raise "IndexError: Index must be int or string". All indexes are
    # thus raw strings.
    event_data = AndroidWebViewCacheEventData()
    event_data.content_length = row['contentlength']
    event_data.query = query
    event_data.url = row['url']

    if row['expires'] is not None:
      date_time = dfdatetime_java_time.JavaTime(timestamp=row['expires'])
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if row['lastmodify'] is not None:
      date_time = dfdatetime_java_time.JavaTime(timestamp=row['lastmodify'])
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidWebViewCachePlugin)
