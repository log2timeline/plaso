# -*- coding: utf-8 -*-
"""The Android WebViewCache database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors

class WebViewCookieExpiryEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for an iOS Kik message event."""

  DATA_TYPE = u'webview:cookie:expiry'

  FORMAT_STRING_PIECES = [
      u'Domain: {domain}',
      u'Path: {path}',
      u'Cookie name: {name}',
      u'Value: {value}',
      u'Secure: {secure}',]

  FORMAT_STRING_SHORT_PIECES = [u'{domain}', u'{name}', u'{value}']

  SOURCE_LONG = u'Android WebView'
  SOURCE_SHORT = u'WebView'

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.CopyToDict()

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WebViewCookieExpiryEventFormatter)