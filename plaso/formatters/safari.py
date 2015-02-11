# -*- coding: utf-8 -*-
"""Formatter for the Safari History events."""

from plaso.formatters import interface
from plaso.formatters import manager


class SafariHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for Safari history events."""

  DATA_TYPE = 'safari:history:visit'

  FORMAT_STRING_PIECES = [
      u'Visited: {url}', u'({title}', u'- {display_title}', ')',
      'Visit Count: {visit_count}']

  SOURCE_LONG = 'Safari History'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(SafariHistoryFormatter)
