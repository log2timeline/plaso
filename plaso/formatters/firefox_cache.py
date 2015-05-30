# -*- coding: utf-8 -*-
"""The Firefox cache record event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class FirefoxCacheFormatter(interface.ConditionalEventFormatter):
  """The Firefox cache record event formatter."""

  DATA_TYPE = u'firefox:cache:record'

  FORMAT_STRING_PIECES = [
      u'Fetched {fetch_count} time(s)',
      u'[{response_code}]',
      u'{request_method}',
      u'"{url}"']

  FORMAT_STRING_SHORT_PIECES = [
      u'[{response_code}]',
      u'{request_method}',
      u'"{url}"']

  SOURCE_LONG = u'Firefox Cache'
  SOURCE_SHORT = u'WEBHIST'


manager.FormattersManager.RegisterFormatter(FirefoxCacheFormatter)
