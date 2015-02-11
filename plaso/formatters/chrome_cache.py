# -*- coding: utf-8 -*-
"""Formatter for Chrome Cache files based-events."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeCacheEntryEventFormatter(interface.ConditionalEventFormatter):
  """Class contains the Chrome Cache Entry event formatter."""

  DATA_TYPE = 'chrome:cache:entry'

  FORMAT_STRING_PIECES = [
      u'Original URL: {original_url}']

  SOURCE_LONG = 'Chrome Cache'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(ChromeCacheEntryEventFormatter)
