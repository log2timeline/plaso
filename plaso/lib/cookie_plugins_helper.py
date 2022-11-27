# -*- coding: utf-8 -*-
"""The cookie plugins helper mix-in."""

# Register the cookie plugins.
from plaso.parsers import cookie_plugins  # pylint: disable=unused-import
from plaso.parsers.cookie_plugins import manager as cookie_plugins_manager


class CookiePluginsHelper(object):
  """Cookie plugins helper mix-in."""

  def __init__(self):
    """Initializes the cookie plugins helper mix-in."""
    super(CookiePluginsHelper, self).__init__()
    self._cookie_plugins = (
        cookie_plugins_manager.CookiePluginsManager.GetPlugins())

  def _ParseCookie(self, parser_mediator, cookie_name, cookie_data, url):
    """Parses a cookie.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      cookie_name (str): the name of the cookie value.
      cookie_data (bytes): the cookie data, as a byte sequence.
      url (str): the full URL or path where the cookie was set.
    """
    for cookie_plugin in self._cookie_plugins:
      if parser_mediator.abort:
        break

      if cookie_name == cookie_plugin.COOKIE_NAME:
        try:
          cookie_plugin.UpdateChainAndProcess(
              parser_mediator, cookie_data=cookie_data, cookie_name=cookie_name,
              url=url)

        except Exception as exception:  # pylint: disable=broad-except
          parser_mediator.ProduceExtractionWarning(
              'plugin: {0:s} unable to parse cookie with error: {1!s}'.format(
                  cookie_plugin.NAME, exception))
