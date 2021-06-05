# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google Chrome cookies database files."""

from dfdatetime import webkit_time as dfdatetime_webkit_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
# Register the cookie plugins.
from plaso.parsers import cookie_plugins  # pylint: disable=unused-import
from plaso.parsers import sqlite
from plaso.parsers.cookie_plugins import manager as cookie_plugins_manager
from plaso.parsers.sqlite_plugins import interface


class ChromeCookieEventData(events.EventData):
  """Chrome Cookie event data.

  Attributes:
    cookie_name (str): name of the cookie.
    host (str): hostname of host that set the cookie value.
    httponly (bool): True if the cookie cannot be accessed through client
        side script.
    path (str): path where the cookie got set.
    persistent (bool): True if the cookie is persistent.
    query (str): SQL query that was used to obtain the event data.
    secure (bool): True if the cookie should only be transmitted over a
        secure channel.
    url (str): URL or path where the cookie got set.
    data (str): value of the cookie.
  """

  DATA_TYPE = 'chrome:cookie:entry'

  def __init__(self):
    """Initializes event data."""
    super(ChromeCookieEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.data = None
    self.host = None
    self.httponly = None
    self.path = None
    self.persistent = None
    self.query = None
    self.secure = None
    self.url = None


class BaseChromeCookiePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Google Chrome cookies database files."""

  # Google Analytics __utmz variable translation.
  GA_UTMZ_TRANSLATION = {
      'utmcsr': 'Last source used to access.',
      'utmccn': 'Ad campaign information.',
      'utmcmd': 'Last type of visit.',
      'utmctr': 'Keywords used to find site.',
      'utmcct': 'Path to the page of referring link.'}

  def __init__(self):
    """Initializes a plugin."""
    super(BaseChromeCookiePlugin, self).__init__()
    self._cookie_plugins = (
        cookie_plugins_manager.CookiePluginsManager.GetPlugins())

  def ParseCookieRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a cookie row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from the query.
    """
    query_hash = hash(query)

    cookie_name = self._GetRowValue(query_hash, row, 'name')
    cookie_data = self._GetRowValue(query_hash, row, 'value')

    hostname = self._GetRowValue(query_hash, row, 'host_key')
    if hostname.startswith('.'):
      hostname = hostname[1:]

    httponly = self._GetRowValue(query_hash, row, 'httponly')
    path = self._GetRowValue(query_hash, row, 'path')
    persistent = self._GetRowValue(query_hash, row, 'persistent')
    secure = self._GetRowValue(query_hash, row, 'secure')

    if secure:
      scheme = 'https'
    else:
      scheme = 'http'

    url = '{0:s}://{1:s}{2:s}'.format(scheme, hostname, path)

    event_data = ChromeCookieEventData()
    event_data.cookie_name = cookie_name
    event_data.data = cookie_data
    event_data.host = hostname
    event_data.httponly = bool(httponly)
    event_data.path = path
    event_data.persistent = bool(persistent)
    event_data.query = query
    event_data.secure = bool(secure)
    event_data.url = url

    timestamp = self._GetRowValue(query_hash, row, 'creation_utc')
    date_time = dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'last_access_utc')
    date_time = dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'expires_utc')
    if timestamp:
      date_time = dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for plugin in self._cookie_plugins:
      if cookie_name != plugin.COOKIE_NAME:
        continue

      try:
        plugin.UpdateChainAndProcess(
            parser_mediator, cookie_data=cookie_data, cookie_name=cookie_name,
            url=url)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning(
            'plugin: {0:s} unable to parse cookie with error: {1!s}'.format(
                plugin.NAME, exception))


class Chrome17CookiePlugin(BaseChromeCookiePlugin):
  """SQLite parser plugin for Google Chrome 17 - 65 cookies database files."""

  NAME = 'chrome_17_cookies'
  DATA_FORMAT = 'Google Chrome 17 - 65 cookies SQLite database file'

  REQUIRED_STRUCTURE = {
      'cookies': frozenset([
          'creation_utc', 'host_key', 'name', 'value', 'path', 'expires_utc',
          'secure', 'httponly', 'last_access_utc', 'has_expires',
          'persistent']),
      'meta': frozenset([])}

  QUERIES = [
      (('SELECT creation_utc, host_key, name, value, path, expires_utc, '
        'secure, httponly, last_access_utc, has_expires, persistent '
        'FROM cookies'), 'ParseCookieRow')]

  SCHEMAS = [{
      'cookies': (
          'CREATE TABLE cookies (creation_utc INTEGER NOT NULL UNIQUE PRIMARY '
          'KEY, host_key TEXT NOT NULL, name TEXT NOT NULL, value TEXT NOT '
          'NULL, path TEXT NOT NULL, expires_utc INTEGER NOT NULL, secure '
          'INTEGER NOT NULL, httponly INTEGER NOT NULL, last_access_utc '
          'INTEGER NOT NULL, has_expires INTEGER DEFAULT 1, persistent '
          'INTEGER DEFAULT 1)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)')}]


class Chrome66CookiePlugin(BaseChromeCookiePlugin):
  """SQLite parser plugin for Google Chrome 66+ cookies database files."""

  NAME = 'chrome_66_cookies'
  DATA_FORMAT = 'Google Chrome 66 and later cookies SQLite database file'

  REQUIRED_STRUCTURE = {
      'cookies': frozenset([
          'creation_utc', 'host_key', 'name', 'value', 'path', 'expires_utc',
          'is_secure', 'is_httponly', 'last_access_utc', 'has_expires',
          'is_persistent']),
      'meta': frozenset([])}

  QUERIES = [
      (('SELECT creation_utc, host_key, name, value, path, expires_utc, '
        'is_secure AS secure, is_httponly AS httponly, last_access_utc, '
        'has_expires, is_persistent AS persistent '
        'FROM cookies'), 'ParseCookieRow')]

  SCHEMAS = [{
      'cookies': (
          'CREATE TABLE cookies (creation_utc INTEGER NOT NULL, host_key TEXT '
          'NOT NULL, name TEXT NOT NULL, value TEXT NOT NULL, path TEXT NOT '
          'NULL, expires_utc INTEGER NOT NULL, is_secure INTEGER NOT NULL, '
          'is_httponly INTEGER NOT NULL, last_access_utc INTEGER NOT NULL, '
          'has_expires INTEGER NOT NULL DEFAULT 1, is_persistent INTEGER NOT '
          'NULL DEFAULT 1, priority INTEGER NOT NULL DEFAULT 1, '
          'encrypted_value BLOB DEFAULT \'\', firstpartyonly INTEGER NOT NULL '
          'DEFAULT 0, UNIQUE (host_key, name, path))'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)')}]


sqlite.SQLiteParser.RegisterPlugins([
    Chrome17CookiePlugin, Chrome66CookiePlugin])
