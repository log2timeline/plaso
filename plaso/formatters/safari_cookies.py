# -*- coding: utf-8 -*-
"""The Safari Binary cookie event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SafaryCookieFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Safari Binary Cookie file entry event."""

  DATA_TYPE = u'safari:cookie:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'<{path}>',
      u'({cookie_name})',
      u'Flags: {flags}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{url}',
      u'({cookie_name})']

  SOURCE_LONG = u'Safari Cookies'
  SOURCE_SHORT = u'WEBHIST'


manager.FormattersManager.RegisterFormatter(SafaryCookieFormatter)
