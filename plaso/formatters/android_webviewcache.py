# -*- coding: utf-8 -*-
"""The Android WebViewCache database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


# TODO: move to android_webview.py.
class AndroidWebViewCacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for Android WebViewCache event data."""

  DATA_TYPE = 'android:webviewcache'

  FORMAT_STRING_PIECES = [
      'URL: {url}',
      'Content Length: {content_length}']

  FORMAT_STRING_SHORT_PIECES = [
      '{url}']

  SOURCE_LONG = 'Android WebViewCache'
  SOURCE_SHORT = 'WebViewCache'


manager.FormattersManager.RegisterFormatter(AndroidWebViewCacheFormatter)
