# -*- coding: utf-8 -*-
"""This file contains a formatter for the Google Chrome cookie."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeCookieFormatter(interface.ConditionalEventFormatter):
  """The event formatter for cookie data in Chrome Cookies database."""

  DATA_TYPE = 'chrome:cookie:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Flags:',
      u'[HTTP only] = {httponly}',
      u'[Persistent] = {persistent}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{host}',
      u'({cookie_name})']

  SOURCE_LONG = 'Chrome Cookies'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(ChromeCookieFormatter)
