# -*- coding: utf-8 -*-
"""The Android WebViewCache database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class WebViewCacheFormatter(interface.ConditionalEventFormatter):
  """Parent class for Android WebViewCache formatters."""

  FORMAT_STRING_PIECES = [
      u'URL: {url}',
      u'Content Length: {content_length}',]

  FORMAT_STRING_SHORT_PIECES = [u'url']

  SOURCE_LONG = u'Android WebViewCache'
  SOURCE_SHORT = u'WebViewCache'


class WebViewCacheURLExpirationEventFormatter(WebViewCacheFormatter):
  """Formatter for an Android WebViewCache URL expiry event."""

  DATA_TYPE = u'android:webviewcache:url_expiry'


class WebViewCacheURLModificationEventFormatter(WebViewCacheFormatter):
  """Formatter for an Android WebViewCache URL expiry event."""

  DATA_TYPE = u'android:webviewcache:url_modification'


manager.FormattersManager.RegisterFormatters([
    WebViewCacheURLExpirationEventFormatter,
    WebViewCacheURLModificationEventFormatter])
