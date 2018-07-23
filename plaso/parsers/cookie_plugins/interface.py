# -*- coding: utf-8 -*-
"""This file contains an interface for browser cookie plugins."""

from __future__ import unicode_literals

import abc

from plaso.lib import errors
from plaso.parsers import plugins


class BaseCookiePlugin(plugins.BasePlugin):
  """A browser cookie plugin for Plaso.

  This is a generic cookie parsing interface that can handle parsing
  cookies from all browsers.
  """
  NAME = 'cookie'
  DESCRIPTION = ''

  # The name of the cookie value that this plugin is designed to parse.
  # This value is used to evaluate whether the plugin is the correct one
  # to parse the browser cookie.
  COOKIE_NAME = ''

  def __init__(self):
    """Initialize the browser cookie plugin."""
    super(BaseCookiePlugin, self).__init__()
    self.cookie_data = ''

  @abc.abstractmethod
  def GetEntries(self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extract and return EventObjects from the data structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cookie_data (Optional[bytes]): cookie data, as a byte sequence.
      url (Optional[str]): URL or path where the cookie was set.
    """

  # pylint: disable=arguments-differ
  def Process(self, parser_mediator, cookie_name, cookie_data, url, **kwargs):
    """Determine if this is the right plugin for this cookie.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cookie_name (str): the name of the cookie value.
      cookie_data (bytes): the cookie data, as a byte sequence.
      url (str): the full URL or path where the cookie was set.

    Raises:
      errors.WrongPlugin: If the cookie name differs from the one
          supplied in COOKIE_NAME.
      ValueError: If cookie_name or cookie_data are not set.
    """
    if cookie_name is None or cookie_data is None:
      raise ValueError('Cookie name or data are not set.')

    if cookie_name != self.COOKIE_NAME:
      raise errors.WrongPlugin(
          'Not the correct cookie plugin for: {0:s} [{1:s}]'.format(
              cookie_name, self.NAME))

    # This will raise if unhandled keyword arguments are passed.
    super(BaseCookiePlugin, self).Process(parser_mediator)

    self.GetEntries(parser_mediator, cookie_data=cookie_data, url=url)
