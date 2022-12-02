# -*- coding: utf-8 -*-
"""This file contains an interface for browser cookie plugins."""

import abc

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.lib import errors
from plaso.parsers import plugins


class BaseCookiePlugin(plugins.BasePlugin):
  """A browser cookie plugin for Plaso.

  This is a generic cookie parsing interface that can handle parsing
  cookies from all browsers.
  """
  NAME = 'cookie_plugin'
  DATA_FORMAT = 'Browser cookie data'

  # The name of the cookie value that this plugin is designed to parse.
  # This value is used to evaluate whether the plugin is the correct one
  # to parse the browser cookie.
  COOKIE_NAME = ''

  @abc.abstractmethod
  def _ParseCookieData(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts events from cookie data.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      cookie_data (Optional[bytes]): cookie data, as a byte sequence.
      url (Optional[str]): URL or path where the cookie was set.
    """

  def _ParseIntegerValue(self, string_value):
    """Parses an integer time.

    Args:
      string_value (str): string value.

    Returns:
      int: integer value or None if not available.
    """
    try:
      return int(string_value, 10)
    except (TypeError, ValueError):
      return None

  def _ParsePosixTime(self, string_value):
    """Parses a POSIX time.

    Args:
      string_value (str): string value.

    Returns:
      dfdatetime.PosixTime: date and time value or None if not available.
    """
    try:
      timestamp = int(string_value, 10)
    except (TypeError, ValueError):
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def _ParsePosixTimeInMilliseconds(self, string_value):
    """Parses a POSIX time in milliseconds.

    Args:
      string_value (str): string value.

    Returns:
      dfdatetime.PosixTimeInMilliseconds: date and time value or None if not
          available.
    """
    try:
      timestamp = int(string_value, 10)
    except (TypeError, ValueError):
      return None

    return dfdatetime_posix_time.PosixTimeInMilliseconds(timestamp=timestamp)

  def _ParsePosixTimeIn100Nanoseconds(self, string_value):
    """Parses a POSIX time in 100 nanoseconds intervals.

    Args:
      string_value (str): string value.

    Returns:
      dfdatetime.PosixTimeInMicroseconds: date and time value or None if not
          available.
    """
    try:
      timestamp = int(string_value, 10)
      # TODO: fix that we're losing precision here.
      timestamp //= 10
    except (TypeError, ValueError):
      return None

    return dfdatetime_posix_time.PosixTimeInMicroseconds(timestamp=timestamp)

  # pylint: disable=arguments-differ
  def Process(self, parser_mediator, cookie_name, cookie_data, url, **kwargs):
    """Extracts events from cookie data.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
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

    self._ParseCookieData(parser_mediator, cookie_data=cookie_data, url=url)
