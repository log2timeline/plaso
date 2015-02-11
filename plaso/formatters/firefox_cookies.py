# -*- coding: utf-8 -*-
"""This file contains a formatter for the Firefox cookie."""

from plaso.formatters import interface
from plaso.formatters import manager


class FirefoxCookieFormatter(interface.ConditionalEventFormatter):
  """The event formatter for cookie data in Firefox Cookies database."""

  DATA_TYPE = 'firefox:cookie:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Flags:',
      u'[HTTP only]: {httponly}',
      u'(GA analysis: {ga_data})']

  FORMAT_STRING_SHORT_PIECES = [
      u'{host}',
      u'({cookie_name})']

  SOURCE_LONG = 'Firefox Cookies'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(FirefoxCookieFormatter)
