# -*- coding: utf-8 -*-
"""SQLite parser plugin for Mozilla Firefox cookies database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import cookie_plugins_helper
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class FirefoxCookieEventData(events.EventData):
  """Firefox Cookie event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): date and time the cookie
        was last accessed.
    cookie_name (str): name field of the cookie.
    creation_time (dfdatetime.DateTimeValues): date and time the cookie
        was created.
    data (str): cookie data.
    expiration_time (dfdatetime.DateTimeValues): date and time the cookie
        expires.
    httponly (bool): True if the cookie cannot be accessed through client
        side script.
    host (str): hostname of host that set the cookie value.
    offset (str): identifier of the row, from which the event data was
        extracted.
    path (str): URI of the page that set the cookie.
    query (str): SQL query that was used to obtain the event data.
    secure (bool): True if the cookie should only be transmitted over a secure
        channel.
  """

  DATA_TYPE = 'firefox:cookie:entry'

  def __init__(self):
    """Initializes event data."""
    super(FirefoxCookieEventData, self).__init__(data_type=self.DATA_TYPE)
    self.access_time = None
    self.cookie_name = None
    self.creation_time = None
    self.data = None
    self.expiration_time = None
    self.host = None
    self.httponly = None
    self.offset = None
    self.path = None
    self.query = None
    self.secure = None
    self.url = None


class BaseFirefoxCookiePlugin(
    interface.SQLitePlugin, cookie_plugins_helper.CookiePluginsHelper):
  """Shared SQLite parser plugin for Mozilla Firefox cookies database files."""

  def _GetPosixTimeDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a POSIX time (in seconds) date and time value from the row.

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

  def _GetPosixTimeInMicrosecondsDateTimeRowValue(
      self, query_hash, row, value_name):
    """Retrieves a POSIX time in microseconds date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTimeInMicroseconds: date and time value or None if not
          available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTimeInMicroseconds(timestamp=timestamp)

  def ParseCookieRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a cookie row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    cookie_data = self._GetRowValue(query_hash, row, 'value')
    cookie_name = self._GetRowValue(query_hash, row, 'name')

    hostname = self._GetRowValue(query_hash, row, 'host')
    if hostname.startswith('.'):
      hostname = hostname[1:]

    is_secure = bool(self._GetRowValue(query_hash, row, 'isSecure'))
    if is_secure:
      url_scheme = 'https'
    else:
      url_scheme = 'http'

    path = self._GetRowValue(query_hash, row, 'path')
    url = '{0:s}://{1:s}{2:s}'.format(url_scheme, hostname, path)

    event_data = FirefoxCookieEventData()
    event_data.access_time = self._GetPosixTimeInMicrosecondsDateTimeRowValue(
        query_hash, row, 'lastAccessed')
    event_data.cookie_name = cookie_name
    event_data.creation_time = self._GetPosixTimeInMicrosecondsDateTimeRowValue(
        query_hash, row, 'creationTime')
    event_data.data = cookie_data
    event_data.host = hostname
    event_data.httponly = bool(self._GetRowValue(query_hash, row, 'isHttpOnly'))
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.path = path
    event_data.query = query
    event_data.secure = is_secure
    event_data.url = url

    # Expiry time (nsCookieService::GetExpiry in
    # netwerk/cookie/nsCookieService.cpp).
    # It's calculated as the difference between the server time and the time
    # the server wants the cookie to expire and adding that difference to the
    # client time. This localizes the client time regardless of whether or not
    # the TZ environment variable was set on the client.

    event_data.expiration_time = self._GetPosixTimeDateTimeRowValue(
        query_hash, row, 'expiry')

    parser_mediator.ProduceEventData(event_data)

    self._ParseCookie(parser_mediator, cookie_name, cookie_data, url)


class FirefoxCookie2Plugin(BaseFirefoxCookiePlugin):
  """SQLite parser plugin for Mozilla Firefox cookies schema 2 databases.

  Also see:
    https://hg.mozilla.org/mozilla-central/file/349a2f003529/netwerk/cookie/nsCookie.h
  """

  NAME = 'firefox_2_cookies'
  DATA_FORMAT = 'Mozilla Firefox cookies SQLite database file version 2'

  REQUIRED_STRUCTURE = {
      'moz_cookies': frozenset([
          'id', 'baseDomain', 'name', 'value', 'host', 'path', 'expiry',
          'lastAccessed', 'creationTime', 'isSecure', 'isHttpOnly'])}

  QUERIES = [
      (('SELECT id, baseDomain, name, value, host, path, expiry, '
        'lastAccessed, creationTime, isSecure, isHttpOnly FROM moz_cookies'),
       'ParseCookieRow')]

  SCHEMAS = [{
      'moz_cookies': (
          'CREATE TABLE moz_cookies (id INTEGER PRIMARY KEY, baseDomain TEXT, '
          'appId INTEGER DEFAULT 0, inBrowserElement INTEGER DEFAULT 0, name '
          'TEXT, value TEXT, host TEXT, path TEXT, expiry INTEGER, '
          'lastAccessed INTEGER, creationTime INTEGER, isSecure INTEGER, '
          'isHttpOnly INTEGER, CONSTRAINT moz_uniqueid UNIQUE (name, host, '
          'path, appId, inBrowserElement))')}]


class FirefoxCookie10Plugin(BaseFirefoxCookiePlugin):
  """SQLite parser plugin for Mozilla Firefox cookies schema 10 databases.
  
  In schema 10 baseDomain was removed.
  
  Also see:
    https://searchfox.org/mozilla-central/source/netwerk/cookie/CookiePersistentStorage.cpp
  """

  NAME = 'firefox_10_cookies'
  DATA_FORMAT = 'Mozilla Firefox cookies SQLite database file version 10'

  REQUIRED_STRUCTURE = {
      'moz_cookies': frozenset([
          'id', 'name', 'value', 'host', 'path', 'expiry',
          'lastAccessed', 'creationTime', 'isSecure', 'isHttpOnly'])}

  QUERIES = [
      (('SELECT id, name, value, host, path, expiry, '
        'lastAccessed, creationTime, isSecure, isHttpOnly FROM moz_cookies'),
       'ParseCookieRow')]

  SCHEMAS = [{
      'moz_cookies': (
          'CREATE TABLE moz_cookies (id INTEGER PRIMARY KEY, '
          'appId INTEGER DEFAULT 0, inBrowserElement INTEGER DEFAULT 0, name '
          'TEXT, value TEXT, host TEXT, path TEXT, expiry INTEGER, '
          'lastAccessed INTEGER, creationTime INTEGER, isSecure INTEGER, '
          'isHttpOnly INTEGER, CONSTRAINT moz_uniqueid UNIQUE (name, host, '
          'path, appId, inBrowserElement))')}]


sqlite.SQLiteParser.RegisterPlugins([
    FirefoxCookie2Plugin, FirefoxCookie10Plugin])
