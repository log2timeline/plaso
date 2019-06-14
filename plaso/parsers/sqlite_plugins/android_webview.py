# -*- coding: utf-8 -*-
"""Parser for Android WebView databases."""

from __future__ import unicode_literals

from dfdatetime import java_time as dfdatetime_java_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
# Register the cookie plugins.
from plaso.parsers import cookie_plugins  # pylint: disable=unused-import
from plaso.parsers import sqlite
from plaso.parsers.cookie_plugins import manager as cookie_plugins_manager
from plaso.parsers.sqlite_plugins import interface


class WebViewCookieEventData(events.EventData):
  """Android WebView cookie event data.

  Attributes:
    cookie_name (str): name of the cookie.
    data (str): data stored in the cookie.
    domain (str): host that set the cookie.
    path (str): path for which the cookie was set.
    secure (bool): True if the cookie should only be transmitted over
        a secure channel.
    url (str): URL of the cookie.
  """

  DATA_TYPE = 'webview:cookie'

  def __init__(self):
    """Initializes event data."""
    super(WebViewCookieEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.data = None
    self.host = None
    self.path = None
    self.secure = None
    self.url = None


class WebViewPlugin(interface.SQLitePlugin):
  """Parser for WebView databases."""

  NAME = 'android_webview'
  DESCRIPTION = 'Parser for Android WebView databases'

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

  def __init__(self):
    """Initializes a plugin object."""
    super(WebViewPlugin, self).__init__()
    self._cookie_plugins = (
        cookie_plugins_manager.CookiePluginsManager.GetPlugins())

  def ParseCookieRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    cookie_name = self._GetRowValue(query_hash, row, 'name')
    cookie_value = self._GetRowValue(query_hash, row, 'value')
    path = self._GetRowValue(query_hash, row, 'path')

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

    event_data = WebViewCookieEventData()
    event_data.cookie_name = cookie_name
    event_data.data = cookie_value
    event_data.host = hostname
    event_data.offset = self._GetRowValue(query_hash, row, '_id')
    event_data.path = path
    event_data.query = query
    event_data.secure = secure
    event_data.url = url

    timestamp = self._GetRowValue(query_hash, row, 'expires')
    if timestamp:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
    else:
      date_time = dfdatetime_semantic_time.SemanticTime('Infinity')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    # Go through all cookie plugins to see if there are is any specific parsing
    # needed.
    for cookie_plugin in self._cookie_plugins:
      try:
        cookie_plugin.UpdateChainAndProcess(
            parser_mediator, cookie_name=cookie_name,
            cookie_data=cookie_value, url=url)
      except errors.WrongPlugin:
        pass


sqlite.SQLiteParser.RegisterPlugin(WebViewPlugin)
