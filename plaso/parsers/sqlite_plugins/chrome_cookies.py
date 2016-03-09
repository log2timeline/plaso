# -*- coding: utf-8 -*-
"""Parser for the Google Chrome Cookie database."""

from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
# Register the cookie plugins.
from plaso.parsers import cookie_plugins  # pylint: disable=unused-import
from plaso.parsers import sqlite
from plaso.parsers.cookie_plugins import manager as cookie_plugins_manager
from plaso.parsers.sqlite_plugins import interface


class ChromeCookieEvent(time_events.WebKitTimeEvent):
  """Convenience class for a Chrome Cookie event."""

  DATA_TYPE = u'chrome:cookie:entry'

  def __init__(
      self, timestamp, usage, hostname, cookie_name, value, path, secure,
      httponly, persistent):
    """Initializes the event.

    Args:
      timestamp: The timestamp value in WebKit format..
      usage: Timestamp description string.
      hostname: The hostname of host that set the cookie value.
      cookie_name: The name field of the cookie.
      value: The value of the cookie.
      path: An URI of the page that set the cookie.
      secure: Indication if this cookie should only be transmitted over a secure
      channel.
      httponly: An indication that the cookie cannot be accessed through client
      side script.
      persistent: A flag indicating cookies persistent value.
    """
    super(ChromeCookieEvent, self).__init__(timestamp, usage)
    if hostname.startswith('.'):
      hostname = hostname[1:]

    self.host = hostname
    self.cookie_name = cookie_name
    self.data = value
    self.path = path
    self.secure = True if secure else False
    self.httponly = True if httponly else False
    self.persistent = True if persistent else False

    if self.secure:
      scheme = u'https'
    else:
      scheme = u'http'

    self.url = u'{0:s}://{1:s}{2:s}'.format(scheme, hostname, path)


class ChromeCookiePlugin(interface.SQLitePlugin):
  """Parse Chrome Cookies file."""

  NAME = u'chrome_cookies'
  DESCRIPTION = u'Parser for Chrome cookies SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT creation_utc, host_key, name, value, path, expires_utc, '
        u'secure, httponly, last_access_utc, has_expires, persistent '
        u'FROM cookies'), u'ParseCookieRow')]

  # The required tables common to Archived History and History.
  REQUIRED_TABLES = frozenset([u'cookies', u'meta'])

  # Point to few sources for URL information.
  URLS = [
      u'http://src.chromium.org/svn/trunk/src/net/cookies/',
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  # Google Analytics __utmz variable translation.
  # Taken from:
  #   http://www.dfinews.com/sites/dfinews.com/files/u739/Tab2Cookies020312.jpg
  GA_UTMZ_TRANSLATION = {
      u'utmcsr': u'Last source used to access.',
      u'utmccn': u'Ad campaign information.',
      u'utmcmd': u'Last type of visit.',
      u'utmctr': u'Keywords used to find site.',
      u'utmcct': u'Path to the page of referring link.'}

  def __init__(self):
    """Initializes a plugin object."""
    super(ChromeCookiePlugin, self).__init__()
    self._cookie_plugins = (
        cookie_plugins_manager.CookiePluginsManager.GetPlugins())

  def ParseCookieRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a cookie row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_object = ChromeCookieEvent(
        row['creation_utc'], eventdata.EventTimestamp.CREATION_TIME,
        row['host_key'], row['name'], row['value'], row['path'],
        row['secure'], row['httponly'], row['persistent'])
    parser_mediator.ProduceEvent(event_object, query=query)

    event_object = ChromeCookieEvent(
        row['last_access_utc'], eventdata.EventTimestamp.ACCESS_TIME,
        row['host_key'], row['name'], row['value'], row['path'],
        row['secure'], row['httponly'], row['persistent'])
    parser_mediator.ProduceEvent(event_object, query=query)

    if row['has_expires']:
      event_object = ChromeCookieEvent(
          row['expires_utc'], u'Cookie Expires',
          row['host_key'], row['name'], row['value'], row['path'],
          row['secure'], row['httponly'], row['persistent'])
      parser_mediator.ProduceEvent(event_object, query=query)

    # Go through all cookie plugins to see if there are is any specific parsing
    # needed.
    hostname = row['host_key']
    if hostname.startswith('.'):
      hostname = hostname[1:]

    url = u'http{0:s}://{1:s}{2:s}'.format(
        u's' if row['secure'] else u'', hostname, row['path'])

    for cookie_plugin in self._cookie_plugins:
      try:
        cookie_plugin.UpdateChainAndProcess(
            parser_mediator, cookie_name=row['name'],
            cookie_data=row['value'], url=url)
      except errors.WrongPlugin:
        pass



sqlite.SQLiteParser.RegisterPlugin(ChromeCookiePlugin)
