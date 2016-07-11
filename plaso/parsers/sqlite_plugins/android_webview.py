# -*- coding: utf-8 -*-
"""Parser for Android WebView databases."""

from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
# Register the cookie plugins.
from plaso.parsers import cookie_plugins  # pylint: disable=unused-import
from plaso.parsers import sqlite
from plaso.parsers.cookie_plugins import manager as cookie_plugins_manager
from plaso.parsers.sqlite_plugins import interface


class WebViewCookieExpiryEvent(time_events.JavaTimeEvent):
  """Convenience class for a WebView cookie expiry event.

  Attributes:
    cookie_name: a string containing the name of the cookie.
    data: a string containing the data stored in the cookie.
    domain: a string containing the host that set the cookie.
    identifier: an integer type containing the identifier of the row containing
                the event information.
    offset: an integer type containing the identifier of the row containing the
            event information.
    path: a string containing the path for which the cookie was set.
    secure: a boolean indicating if the cookie should only be transmitted over
            a secure channel.
  """

  DATA_TYPE = u'webview:cookie:expiry'

  def __init__(
      self, timestamp, identifier, domain, cookie_name, value, path, secure):
    """Initializes the event.

    Args:
      timestamp: the Java timestamp which is an integer containing the number
                 of milliseconds since January 1, 1970, 00:00:00 UTC.
      identifier: an integer containing the identifier of the row containing
                the event information.
      domain: the hostname of host that set the cookie value.
      cookie_name: the name field of the cookie.
      value: string containing the value of the cookie.
      path: a string containing the path for which the cookie was set.
      secure: boolean indicating that the cookie should only be transmitted
              over a secure channel.
    """
    super(WebViewCookieExpiryEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.EXPIRATION_TIME)
    self.cookie_name = cookie_name
    self.data = value
    self.host = domain
    self.identifier = identifier
    self.offset = identifier
    self.path = path
    self.secure = True if secure else False

    if self.secure:
      scheme = u'https'
    else:
      scheme = u'http'

    self.url = u'{0:s}://{1:s}{2:s}'.format(scheme, domain, path)


class WebViewPlugin(interface.SQLitePlugin):
  """Parser for WebView databases."""

  NAME = u'android_webview'
  DESCRIPTION = u'Parser for Android WebView databases'

  REQUIRED_TABLES = frozenset([u'android_metadata', u'cookies'])

  QUERIES = frozenset([
      (u'SELECT _id, name, value, domain, expires, path, secure FROM cookies',
       u'ParseCookieRow')])

  def __init__(self):
    """Initializes a plugin object."""
    super(WebViewPlugin, self).__init__()
    self._cookie_plugins = (
        cookie_plugins_manager.CookiePluginsManager.GetPlugins())

  def ParseCookieRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a row from the database.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string']
    # and will raise "IndexError: Index must be int or string". All indexes are
    # thus raw strings.

    # The WebView database stores the secure flag as a integer type,
    # but we represent it as a boolean.
    secure = row['secure'] != 0
    # TODO: It would be good to have some way of representing "infinity"
    # for cookies that have no expiry.
    if row['expires']:
      event = WebViewCookieExpiryEvent(
          row['expires'], row['_id'], row['domain'], row['name'],
          row['value'], row['path'], secure)
      parser_mediator.ProduceEvent(event, query=query)

    # Go through all cookie plugins to see if there are is any specific parsing
    # needed.
    hostname = row['domain']
    if hostname.startswith('.'):
      hostname = hostname[1:]

    url = u'http{0:s}://{1:s}{2:s}'.format(
        u's' if secure else u'', hostname, row['path'])

    for cookie_plugin in self._cookie_plugins:
      try:
        cookie_plugin.UpdateChainAndProcess(
            parser_mediator, cookie_name=row['name'],
            cookie_data=row['value'], url=url)
      except errors.WrongPlugin:
        pass


sqlite.SQLiteParser.RegisterPlugin(WebViewPlugin)
