# -*- coding: utf-8 -*-
"""Parser for the Firefox Cookie database."""

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
# Register the cookie plugins.
from plaso.parsers import cookie_plugins  # pylint: disable=unused-import
from plaso.parsers import sqlite
from plaso.parsers.cookie_plugins import manager as cookie_plugins_manager
from plaso.parsers.sqlite_plugins import interface


class FirefoxCookieEvent(time_events.TimestampEvent):
  """Convenience class for a Firefox Cookie event."""

  DATA_TYPE = u'firefox:cookie:entry'

  def __init__(
      self, timestamp, usage, identifier, hostname, cookie_name, value, path,
      secure, httponly):
    """Initializes the event.

    Args:
      timestamp: The timestamp value in WebKit format..
      usage: Timestamp description string.
      identifier: The row identifier.
      hostname: The hostname of host that set the cookie value.
      cookie_name: The name field of the cookie.
      value: The value of the cookie.
      path: An URI of the page that set the cookie.
      secure: Indication if this cookie should only be transmitted over a secure
              channel.
      httponly: An indication that the cookie cannot be accessed through client
                side script.
    """
    super(FirefoxCookieEvent, self).__init__(timestamp, usage)
    if hostname.startswith('.'):
      hostname = hostname[1:]

    self.offset = identifier
    self.host = hostname
    self.cookie_name = cookie_name
    self.data = value
    self.path = path
    self.secure = True if secure else False
    self.httponly = True if httponly else False

    if self.secure:
      scheme = u'https'
    else:
      scheme = u'http'

    self.url = u'{0:s}://{1:s}{2:s}'.format(scheme, hostname, path)


class FirefoxCookiePlugin(interface.SQLitePlugin):
  """Parse Firefox Cookies file."""

  NAME = u'firefox_cookies'
  DESCRIPTION = u'Parser for Firefox cookies SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT id, baseDomain, name, value, host, path, expiry, '
        u'lastAccessed, creationTime, isSecure, isHttpOnly FROM moz_cookies'),
       u'ParseCookieRow')]

  # The required tables common to Archived History and History.
  REQUIRED_TABLES = frozenset([u'moz_cookies'])

  # Point to few sources for URL information.
  URLS = [
      (u'https://hg.mozilla.org/mozilla-central/file/349a2f003529/netwerk/'
       u'cookie/nsCookie.h')]

  def __init__(self):
    """Initializes a plugin object."""
    super(FirefoxCookiePlugin, self).__init__()
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

    if row['creationTime']:
      event_object = FirefoxCookieEvent(
          row['creationTime'], eventdata.EventTimestamp.CREATION_TIME,
          row['id'], row['host'], row['name'], row['value'], row['path'],
          row['isSecure'], row['isHttpOnly'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['lastAccessed']:
      event_object = FirefoxCookieEvent(
          row['lastAccessed'], eventdata.EventTimestamp.ACCESS_TIME,
          row['id'], row['host'], row['name'], row['value'], row['path'],
          row['isSecure'], row['isHttpOnly'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['expiry']:
      # Expiry time (nsCookieService::GetExpiry in
      # netwerk/cookie/nsCookieService.cpp).
      # It's calculated as the difference between the server time and the time
      # the server wants the cookie to expire and adding that difference to the
      # client time. This localizes the client time regardless of whether or not
      # the TZ environment variable was set on the client.
      timestamp = timelib.Timestamp.FromPosixTime(row['expiry'])
      event_object = FirefoxCookieEvent(
          timestamp, u'Cookie Expires', row['id'], row['host'], row['name'],
          row['value'], row['path'], row['isSecure'], row['isHttpOnly'])
      parser_mediator.ProduceEvent(event_object, query=query)

    # Go through all cookie plugins to see if there are is any specific parsing
    # needed.
    hostname = row['host']
    if hostname.startswith('.'):
      hostname = hostname[1:]
    url = u'http{0:s}://{1:s}{2:s}'.format(
        u's' if row['isSecure'] else u'', hostname, row['path'])

    for cookie_plugin in self._cookie_plugins:
      try:
        cookie_plugin.UpdateChainAndProcess(
            parser_mediator, cookie_name=row['name'],
            cookie_data=row['value'], url=url)
      except errors.WrongPlugin:
        pass


sqlite.SQLiteParser.RegisterPlugin(FirefoxCookiePlugin)
