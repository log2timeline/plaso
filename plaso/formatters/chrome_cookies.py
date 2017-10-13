# -*- coding: utf-8 -*-
"""The Google Chrome cookies database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeCookieFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome cookie event."""

  DATA_TYPE = 'chrome:cookie:entry'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({cookie_name})',
      'Flags:',
      '[HTTP only] = {httponly}',
      '[Persistent] = {persistent}']

  FORMAT_STRING_SHORT_PIECES = [
      '{host}',
      '({cookie_name})']

  SOURCE_LONG = 'Chrome Cookies'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(ChromeCookieFormatter)
