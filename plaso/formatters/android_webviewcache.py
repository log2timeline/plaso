# -*- coding: utf-8 -*-
"""The Android WebViewCache database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors

class WebViewCacheFormatter(interface.ConditionalEventFormatter):
  """Parent class for Android WebViewCache formatters."""

  FORMAT_STRING_PIECES = [
      u'URL: {url}',
      u'Content Length: {content_length}',]

  FORMAT_STRING_SHORT_PIECES = [u'url']

  SOURCE_LONG = u'Android WebViewCache'
  SOURCE_SHORT = u'WebViewCache'

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


class WebViewCacheURLExpirationEventFormatter(WebViewCacheFormatter):
  """Formatter for an Android WebViewCache URL expiry event."""

  DATA_TYPE = u'android:webviewcache:url_expiry'


class WebViewCacheURLModificationEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Android WebViewCache URL expiry event."""

  DATA_TYPE = u'android:webviewcache:url_modification'


manager.FormattersManager.RegisterFormatters([
    WebViewCacheURLExpirationEventFormatter,
    WebViewCacheURLModificationEventFormatter])
