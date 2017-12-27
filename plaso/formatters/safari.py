# -*- coding: utf-8 -*-
"""The Safari history event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SafariHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Safari history event."""

  DATA_TYPE = 'safari:history:visit'

  FORMAT_STRING_PIECES = [
      'Visited: {url}',
      '({title}',
      '- {display_title}',
      ')',
      'Visit Count: {visit_count}']

  SOURCE_LONG = 'Safari History'
  SOURCE_SHORT = 'WEBHIST'


class SafariHistoryFormatterSqlite(interface.ConditionalEventFormatter):
  """Formatter for a Safari history event from Sqlite History.db"""

  DATA_TYPE = 'safari:history:visit_sqlite'

  FORMAT_STRING_PIECES = [
      'URL: {url}',
      'Title: ({title})',
      '[count: {visit_count}]',
      'http_non_get: {was_http_non_get}']


  SOURCE_LONG = 'Safari History'
  SOURCE_SHORT = 'WEBHIST'

manager.FormattersManager.RegisterFormatters([
    SafariHistoryFormatter, SafariHistoryFormatterSqlite])
