# -*- coding: utf-8 -*-
"""The Android WebViewCache database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


# TODO: move to android_webview.py.
class AndroidWebViewCacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for Android WebViewCache event data."""

  DATA_TYPE = u'android:webviewcache'

  FORMAT_STRING_PIECES = [
      u'URL: {url}',
      u'Content Length: {content_length}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{url}']

  SOURCE_LONG = u'Android WebViewCache'
  SOURCE_SHORT = u'WebViewCache'


manager.FormattersManager.RegisterFormatter(AndroidWebViewCacheFormatter)
