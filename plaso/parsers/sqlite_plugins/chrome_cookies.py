# -*- coding: utf-8 -*-
"""Parser for the Google Chrome Cookie database."""

from plaso.containers import time_events
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
      self, timestamp, timestamp_description, hostname, cookie_name, value,
      path, secure, httponly, persistent, url):
    """Initializes the event.

    Args:
      webkit_time (int): WebKit time value.
      timestamp_description (str): description of the usage of the timestamp
          value.
      hostname (str): hostname of host that set the cookie value.
      cookie_name (str): name of the cookie.
      value (str): value of the cookie.
      path (str): path where the cookie got set.
      secure (bool): True if the cookie should only be transmitted over
          a secure channel.
      httponly (bool): True if the cookie cannot be accessed through client
          side script.
      persistent (bool): True if the cookie is persistent.
      url (str): URL or path where the cookie got set.
    """
    super(ChromeCookieEvent, self).__init__(timestamp, timestamp_description)
    self.cookie_name = cookie_name
    self.data = value
    self.host = hostname
    self.httponly = True if httponly else False
    self.path = path
    self.persistent = True if persistent else False
    self.secure = True if secure else False
    self.url = url


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
    """Initializes a plugin."""
    super(ChromeCookiePlugin, self).__init__()
    self._cookie_plugins = (
        cookie_plugins_manager.CookiePluginsManager.GetPlugins())

  def ParseCookieRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a cookie row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    cookie_name = row['name']

    hostname = row['host_key']
    if hostname.startswith('.'):
      hostname = hostname[1:]

    if row['secure']:
      scheme = u'https'
    else:
      scheme = u'http'

    url = u'{0:s}://{1:s}{2:s}'.format(scheme, hostname, row['path'])

    event_object = ChromeCookieEvent(
        row['creation_utc'], eventdata.EventTimestamp.CREATION_TIME,
        hostname, cookie_name, row['value'], row['path'],
        row['secure'], row['httponly'], row['persistent'], url)
    parser_mediator.ProduceEvent(event_object, query=query)

    event_object = ChromeCookieEvent(
        row['last_access_utc'], eventdata.EventTimestamp.ACCESS_TIME,
        hostname, cookie_name, row['value'], row['path'],
        row['secure'], row['httponly'], row['persistent'], url)
    parser_mediator.ProduceEvent(event_object, query=query)

    if row['has_expires']:
      event_object = ChromeCookieEvent(
          row['expires_utc'], u'Cookie Expires',
          hostname, cookie_name, row['value'], row['path'],
          row['secure'], row['httponly'], row['persistent'], url)
      parser_mediator.ProduceEvent(event_object, query=query)

    for plugin in self._cookie_plugins:
      if cookie_name != plugin.COOKIE_NAME:
        continue

      try:
        plugin.UpdateChainAndProcess(
            parser_mediator, cookie_data=row['value'], cookie_name=cookie_name,
            url=url)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionError(
            u'plugin: {0:s} unable to parse cookie with error: {1:s}'.format(
                plugin.NAME, exception))


sqlite.SQLiteParser.RegisterPlugin(ChromeCookiePlugin)
