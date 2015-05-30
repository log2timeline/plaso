# -*- coding: utf-8 -*-
"""The PL/SQL Recall event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class PlsRecallFormatter(interface.EventFormatter):
  """Formatter for a PL/SQL Recall file container event."""
  DATA_TYPE = u'PLSRecall:event'
  SOURCE_LONG = u'PL/SQL Developer Recall file'
  SOURCE_SHORT = u'PLSRecall'

  # The format string.
  FORMAT_STRING = (
      u'Sequence #{sequence} User: {username} Database Name: {database_name} '
      u'Query: {query}')
  FORMAT_STRING_SHORT = u'{sequence} {username} {database_name} {query}'


manager.FormattersManager.RegisterFormatter(PlsRecallFormatter)
