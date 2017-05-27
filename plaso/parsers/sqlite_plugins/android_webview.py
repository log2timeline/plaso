# -*- coding: utf-8 -*-
"""Parser for Android WebView databases."""

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

  DATA_TYPE = u'webview:cookie'

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

  NAME = u'android_webview'
  DESCRIPTION = u'Parser for Android WebView databases'

  REQUIRED_TABLES = frozenset([u'android_metadata', u'cookies'])

  QUERIES = frozenset([
      (u'SELECT _id, name, value, domain, expires, path, secure FROM cookies',
       u'ParseCookieRow')])

  SCHEMAS = [{
      u'android_metadata': (
          u'CREATE TABLE android_metadata (locale TEXT)'),
      u'cookies': (
          u'CREATE TABLE cookies (_id INTEGER PRIMARY KEY, name TEXT, value '
          u'TEXT, domain TEXT, path TEXT, expires INTEGER, secure INTEGER)'),
      u'formdata': (
          u'CREATE TABLE formdata (_id INTEGER PRIMARY KEY, urlid INTEGER, '
          u'name TEXT, value TEXT, UNIQUE (urlid, name, value) ON CONFLICT '
          u'IGNORE)'),
      u'formurl': (
          u'CREATE TABLE formurl (_id INTEGER PRIMARY KEY, url TEXT)'),
      u'httpauth': (
          u'CREATE TABLE httpauth (_id INTEGER PRIMARY KEY, host TEXT, realm '
          u'TEXT, username TEXT, password TEXT, UNIQUE (host, realm) ON '
          u'CONFLICT REPLACE)'),
      u'password': (
          u'CREATE TABLE password (_id INTEGER PRIMARY KEY, host TEXT, '
          u'username TEXT, password TEXT, UNIQUE (host, username) ON CONFLICT '
          u'REPLACE)')}]

  def __init__(self):
    """Initializes a plugin object."""
    super(WebViewPlugin, self).__init__()
    self._cookie_plugins = (
        cookie_plugins_manager.CookiePluginsManager.GetPlugins())

  def ParseCookieRow(self, parser_mediator, row, query=None, **unused_kwargs):
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

    cookie_name = row['name']
    cookie_value = row['value']
    path = row['path']

    hostname = row['domain']
    if hostname.startswith('.'):
      hostname = hostname[1:]

    # The WebView database stores the secure flag as a integer type,
    # but we represent it as a boolean.
    secure = row['secure'] != 0

    if secure:
      scheme = u'https'
    else:
      scheme = u'http'

    url = u'{0:s}://{1:s}{2:s}'.format(scheme, hostname, path)

    timestamp = row['expires']
    if timestamp:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
    else:
      date_time = dfdatetime_semantic_time.SemanticTime(u'Infinity')

    event_data = WebViewCookieEventData()
    event_data.cookie_name = cookie_name
    event_data.data = cookie_value
    event_data.host = hostname
    event_data.offset = row['_id']
    event_data.path = path
    event_data.query = query
    event_data.secure = secure
    event_data.url = url

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
