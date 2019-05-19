# -*- coding: utf-8 -*-
"""The Safari Binary cookie event formatter."""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.formatters import interface
from plaso.formatters import manager


class SafariCookieFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Safari Binary Cookie file entry event."""

  DATA_TYPE = 'safari:cookie:entry'

  FORMAT_STRING_PIECES = [
      '{url}',
      '<{path}>',
      '({cookie_name})',
      'Flags: {flags}']

  FORMAT_STRING_SHORT_PIECES = [
      '{url}',
      '({cookie_name})']

  SOURCE_LONG = 'Safari Cookies'
  SOURCE_SHORT = 'WEBHIST'

  _COOKIE_FLAGS = {
      1: 'Secure',
      2: 'Unknown',
      4: 'HttpOnly'}

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    cookie_flags = event_values.get('flags', None)
    if cookie_flags == 0:
      del event_values['flags']
    elif cookie_flags:
      flags = []
      for flag_value, flag_description in iter(self._COOKIE_FLAGS.items()):
        if cookie_flags & flag_value:
          flags.append(flag_description)

      event_values['flags'] = '|'.join(flags)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(SafariCookieFormatter)
