# -*- coding: utf-8 -*-
"""Formatter for PL-Sql Recall events."""

from plaso.formatters import interface
from plaso.formatters import manager


class PlsRecallFormatter(interface.EventFormatter):
  """Formatter for a for a PL-Sql Recall file container."""
  DATA_TYPE = 'PLSRecall:event'
  SOURCE_LONG = 'PL-Sql Developer Recall file'
  SOURCE_SHORT = 'PLSRecall'

  # The format string.
  FORMAT_STRING = (
      u'Sequence #{sequence} User: {username} Database Name: {database_name} '
      u'Query: {query}')
  FORMAT_STRING_SHORT = u'{sequence} {username} {database_name} {query}'


manager.FormattersManager.RegisterFormatter(PlsRecallFormatter)
