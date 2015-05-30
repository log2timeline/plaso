# -*- coding: utf-8 -*-
"""The Safari history event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SafariHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Safari history event."""

  DATA_TYPE = u'safari:history:visit'

  FORMAT_STRING_PIECES = [
      u'Visited: {url}',
      u'({title}',
      u'- {display_title}',
      u')',
      u'Visit Count: {visit_count}']

  SOURCE_LONG = u'Safari History'
  SOURCE_SHORT = u'WEBHIST'


manager.FormattersManager.RegisterFormatter(SafariHistoryFormatter)
