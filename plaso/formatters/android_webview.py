# -*- coding: utf-8 -*-
"""The Android WebView database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class AndroidWebViewCookieEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for Android WebView Cookie event data."""

  DATA_TYPE = 'webview:cookie'

  FORMAT_STRING_PIECES = [
      'Domain: {domain}',
      'Path: {path}',
      'Cookie name: {name}',
      'Value: {value}',
      'Secure: {secure}',]

  FORMAT_STRING_SHORT_PIECES = [
      '{domain}',
      '{name}',
      '{value}']

  SOURCE_LONG = 'Android WebView'
  SOURCE_SHORT = 'WebView'


manager.FormattersManager.RegisterFormatter(AndroidWebViewCookieEventFormatter)
