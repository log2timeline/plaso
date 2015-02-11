# -*- coding: utf-8 -*-
"""Formatter for Firefox cache records."""

from plaso.formatters import interface
from plaso.formatters import manager

class FirefoxCacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for Firefox cache record."""

  DATA_TYPE = 'firefox:cache:record'

  FORMAT_STRING_PIECES = [
      u'Fetched {fetch_count} time(s)',
      u'[{response_code}]',
      u'{request_method}',
      u'"{url}"']

  FORMAT_STRING_SHORT_PIECES = [
      u'[{response_code}]',
      u'{request_method}',
      u'"{url}"']

  SOURCE_LONG = 'Firefox Cache'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(FirefoxCacheFormatter)
