# -*- coding: utf-8 -*-
"""The Android WebViewCache database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager

class WebViewCookieExpiryEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Android WebView Cookie Expiry event."""

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


manager.FormattersManager.RegisterFormatter(WebViewCookieExpiryEventFormatter)
