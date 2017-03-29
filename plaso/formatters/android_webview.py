# -*- coding: utf-8 -*-
"""The Android WebView database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class AndroidWebViewCookieEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for Android WebView Cookie event data."""

  DATA_TYPE = u'webview:cookie'

  FORMAT_STRING_PIECES = [
      u'Domain: {domain}',
      u'Path: {path}',
      u'Cookie name: {name}',
      u'Value: {value}',
      u'Secure: {secure}',]

  FORMAT_STRING_SHORT_PIECES = [
      u'{domain}',
      u'{name}',
      u'{value}']

  SOURCE_LONG = u'Android WebView'
  SOURCE_SHORT = u'WebView'


manager.FormattersManager.RegisterFormatter(AndroidWebViewCookieEventFormatter)
