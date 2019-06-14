# -*- coding: utf-8 -*-
"""Parser for the Firefox Cookie database."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
# Register the cookie plugins.
from plaso.parsers import cookie_plugins  # pylint: disable=unused-import
from plaso.parsers import sqlite
from plaso.parsers.cookie_plugins import manager as cookie_plugins_manager
from plaso.parsers.sqlite_plugins import interface


class FirefoxCookieEventData(events.EventData):
  """Firefox Cookie event data.

  Attributes:
    cookie_name (str): name field of the cookie.
    data (str): cookie data.
    httponly (bool): True if the cookie cannot be accessed through client
        side script.
    host (str): hostname of host that set the cookie value.
    path (str): URI of the page that set the cookie.
    secure (bool): True if the cookie should only be transmitted over a secure
        channel.
  """

  DATA_TYPE = 'firefox:cookie:entry'

  def __init__(self):
    """Initializes event data."""
    super(FirefoxCookieEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.data = None
    self.host = None
    self.httponly = None
    self.path = None
    self.secure = None
    self.url = None


class FirefoxCookiePlugin(interface.SQLitePlugin):
  """Parser for the Firefox Cookie database."""

  NAME = 'firefox_cookies'
  DESCRIPTION = 'Parser for Firefox cookies SQLite database files.'

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

  # Point to few sources for URL information.
  URLS = [
      ('https://hg.mozilla.org/mozilla-central/file/349a2f003529/netwerk/'
       'cookie/nsCookie.h')]

  def __init__(self):
    """Initializes a Firefox Cookies database SQLite parser plugin."""
    super(FirefoxCookiePlugin, self).__init__()
    self._cookie_plugins = (
        cookie_plugins_manager.CookiePluginsManager.GetPlugins())

  def ParseCookieRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a cookie row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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
    event_data.cookie_name = cookie_name
    event_data.data = cookie_data
    event_data.host = hostname
    event_data.httponly = bool(self._GetRowValue(query_hash, row, 'isHttpOnly'))
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.path = path
    event_data.query = query
    event_data.secure = is_secure
    event_data.url = url

    timestamp = self._GetRowValue(query_hash, row, 'creationTime')
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'lastAccessed')
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'expiry')
    if timestamp:
      # Expiry time (nsCookieService::GetExpiry in
      # netwerk/cookie/nsCookieService.cpp).
      # It's calculated as the difference between the server time and the time
      # the server wants the cookie to expire and adding that difference to the
      # client time. This localizes the client time regardless of whether or not
      # the TZ environment variable was set on the client.

      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    # Go through all cookie plugins to see if there are is any specific parsing
    # needed.
    for cookie_plugin in self._cookie_plugins:
      try:
        cookie_plugin.UpdateChainAndProcess(
            parser_mediator, cookie_name=cookie_name, cookie_data=cookie_data,
            url=url)
      except errors.WrongPlugin:
        pass


sqlite.SQLiteParser.RegisterPlugin(FirefoxCookiePlugin)
