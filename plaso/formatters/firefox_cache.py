# -*- coding: utf-8 -*-
"""The Firefox cache record event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class FirefoxCacheFormatter(interface.ConditionalEventFormatter):
  """The Firefox cache record event formatter."""

  DATA_TYPE = 'firefox:cache:record'

  FORMAT_STRING_PIECES = [
      'Fetched {fetch_count} time(s)',
      '[{response_code}]',
      '{request_method}',
      '"{url}"']

  FORMAT_STRING_SHORT_PIECES = [
      '[{response_code}]',
      '{request_method}',
      '"{url}"']

  SOURCE_LONG = 'Firefox Cache'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(FirefoxCacheFormatter)
