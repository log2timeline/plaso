# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android WebView database files."""

from dfdatetime import java_time as dfdatetime_java_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.lib import cookie_plugins_helper
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidWebViewCookieEventData(events.EventData):
  """Android WebView cookie event data.

  Attributes:
    cookie_name (str): name of the cookie.
    data (str): data stored in the cookie.
    expiration_time (dfdatetime.DateTimeValues): date and time the cache
        entry expires.
    host (str): host that set the cookie.
    offset (str): identifier of the row, from which the event data was
        extracted.
    path (str): path for which the cookie was set.
    query (str): SQL query that was used to obtain the event data.
    secure (bool): True if the cookie should only be transmitted over
        a secure channel.
    url (str): URL of the cookie.
  """

  DATA_TYPE = 'android:webview:cookie'

  def __init__(self):
    """Initializes event data."""
    super(AndroidWebViewCookieEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.data = None
    self.expiration_time = None
    self.host = None
    self.offset = None
    self.path = None
    self.query = None
    self.secure = None
    self.url = None


class AndroidWebViewPlugin(
    interface.SQLitePlugin, cookie_plugins_helper.CookiePluginsHelper):
  """SQLite parser plugin for Android WebView database files."""

  NAME = 'android_webview'
  DATA_FORMAT = 'Android WebView SQLite database file'

  REQUIRED_STRUCTURE = {
      'android_metadata': frozenset([]),
      'cookies': frozenset([
          '_id', 'name', 'value', 'domain', 'expires', 'path', 'secure'])}

  QUERIES = frozenset([
      ('SELECT _id, name, value, domain, expires, path, secure FROM cookies',
       'ParseCookieRow')])

  SCHEMAS = [{
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT)'),
      'cookies': (
          'CREATE TABLE cookies (_id INTEGER PRIMARY KEY, name TEXT, value '
          'TEXT, domain TEXT, path TEXT, expires INTEGER, secure INTEGER)'),
      'formdata': (
          'CREATE TABLE formdata (_id INTEGER PRIMARY KEY, urlid INTEGER, '
          'name TEXT, value TEXT, UNIQUE (urlid, name, value) ON CONFLICT '
          'IGNORE)'),
      'formurl': (
          'CREATE TABLE formurl (_id INTEGER PRIMARY KEY, url TEXT)'),
      'httpauth': (
          'CREATE TABLE httpauth (_id INTEGER PRIMARY KEY, host TEXT, realm '
          'TEXT, username TEXT, password TEXT, UNIQUE (host, realm) ON '
          'CONFLICT REPLACE)'),
      'password': (
          'CREATE TABLE password (_id INTEGER PRIMARY KEY, host TEXT, '
          'username TEXT, password TEXT, UNIQUE (host, username) ON CONFLICT '
          'REPLACE)')}]

  def ParseCookieRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    cookie_name = self._GetRowValue(query_hash, row, 'name')
    cookie_data = self._GetRowValue(query_hash, row, 'value')
    path = self._GetRowValue(query_hash, row, 'path')
    timestamp = self._GetRowValue(query_hash, row, 'expires')

    if timestamp:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
    else:
      date_time = dfdatetime_semantic_time.SemanticTime('Infinity')

    hostname = self._GetRowValue(query_hash, row, 'domain')
    if hostname.startswith('.'):
      hostname = hostname[1:]

    secure = self._GetRowValue(query_hash, row, 'secure')
    # The WebView database stores the secure flag as a integer type,
    # but we represent it as a boolean.
    secure = secure != 0

    if secure:
      scheme = 'https'
    else:
      scheme = 'http'

    url = '{0:s}://{1:s}{2:s}'.format(scheme, hostname, path)

    event_data = AndroidWebViewCookieEventData()
    event_data.cookie_name = cookie_name
    event_data.data = cookie_data
    event_data.expiration_time = date_time
    event_data.host = hostname
    event_data.offset = self._GetRowValue(query_hash, row, '_id')
    event_data.path = path
    event_data.query = query
    event_data.secure = secure
    event_data.url = url

    parser_mediator.ProduceEventData(event_data)

    self._ParseCookie(parser_mediator, cookie_name, cookie_data, url)


sqlite.SQLiteParser.RegisterPlugin(AndroidWebViewPlugin)
