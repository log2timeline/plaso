# -*- coding: utf-8 -*-
"""The Google Chrome cookies database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeCookieFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome cookie event."""

  DATA_TYPE = u'chrome:cookie:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Flags:',
      u'[HTTP only] = {httponly}',
      u'[Persistent] = {persistent}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{host}',
      u'({cookie_name})']

  SOURCE_LONG = u'Chrome Cookies'
  SOURCE_SHORT = u'WEBHIST'


manager.FormattersManager.RegisterFormatter(ChromeCookieFormatter)
