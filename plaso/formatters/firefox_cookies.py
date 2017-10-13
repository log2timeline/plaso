# -*- coding: utf-8 -*-
"""The Firefox cookie entry event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class FirefoxCookieFormatter(interface.ConditionalEventFormatter):
  """The Firefox cookie entry event formatter."""

  DATA_TYPE = 'firefox:cookie:entry'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({cookie_name})',
      'Flags:',
      '[HTTP only]: {httponly}',
      '(GA analysis: {ga_data})']

  FORMAT_STRING_SHORT_PIECES = [
      '{host}',
      '({cookie_name})']

  SOURCE_LONG = 'Firefox Cookies'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(FirefoxCookieFormatter)
