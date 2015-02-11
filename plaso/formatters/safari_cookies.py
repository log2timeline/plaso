# -*- coding: utf-8 -*-
"""This file contains a formatter for the Safari Binary cookie."""

from plaso.formatters import interface
from plaso.formatters import manager


class SafaryCookieFormatter(interface.ConditionalEventFormatter):
  """The event formatter for cookie data in Safari Binary Cookie file."""

  DATA_TYPE = 'safari:cookie:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'<{path}>',
      u'({cookie_name})',
      u'Flags: {flags}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{url}',
      u'({cookie_name})']

  SOURCE_LONG = 'Safari Cookies'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(SafaryCookieFormatter)
