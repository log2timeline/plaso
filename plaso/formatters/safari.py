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
  """ Formatter for a Safari history event for Sqlite History.db"""

  DATA_TYPE = u'safari:history:visit_sqlite'

  FORMAT_STRING_PIECES = [
      u'URL: {url}',
      u'Title: ({title})',
      u'[count: {visit_count}]',
      u'Host: {host}',
      u'http_non_get: {was_http_non_get}']


  SOURCE_LONG = u'Safari History'
  SOURCE_SHORT = u'WEBHIST'

manager.FormattersManager.RegisterFormatters([
    SafariHistoryFormatter, SafariHistoryFormatterSqlite])
