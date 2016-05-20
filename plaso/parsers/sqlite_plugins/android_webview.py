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
  """Convenience class for a Webview cookie expiry event."""

  DATA_TYPE = u'webview:cookie:expiry'

  def __init__(self, timestamp, identifier, domain, cookie_name, value, path,
               secure):
    """Initializes the event.

    Args:
      timestamp: The timestamp value in WebKit format..
      identifier: The row identifier.
      domain: The hostname of host that set the cookie value.
      cookie_name: The name field of the cookie.
      value: The value of the cookie.
      secure: Indication if this cookie should only be transmitted over a secure
              channel.
    """
    super(WebViewCookieExpiryEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.EXPIRATION_TIME)
    self.identifier = identifier
    self.offset = identifier
    self.host = domain
    self.cookie_name = cookie_name
    self.data = value
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
    domain = row['domain']
    if domain and domain.startswith('.'):
      domain = domain[1:]
    # TODO: It would be good to have some way of representing "infinity"
    # for cookies that have no expiry.
    if row['expires']:
      event = WebViewCookieExpiryEvent(
          row['expires'], row['_id'], domain, row['name'],
          row['value'], row['path'], row['secure'])
      parser_mediator.ProduceEvent(event, query=query)

    for cookie_plugin in self._cookie_plugins:
      try:
        cookie_plugin.UpdateChainAndProcess(
            parser_mediator, cookie_name=row['name'],
            cookie_data=row['value'], url=domain)
      except errors.WrongPlugin:
        pass


sqlite.SQLiteParser.RegisterPlugin(WebViewPlugin)
