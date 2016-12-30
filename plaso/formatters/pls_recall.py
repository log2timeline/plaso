# -*- coding: utf-8 -*-
"""The PL/SQL Recall event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class PlsRecallFormatter(interface.ConditionalEventFormatter):
  """Formatter for a PL/SQL Recall file container event."""

  DATA_TYPE = u'PLSRecall:event'
  SOURCE_LONG = u'PL/SQL Developer Recall file'
  SOURCE_SHORT = u'PLSRecall'

  FORMAT_STRING_PIECES = [
      u'Sequence number: {sequence_number}',
      u'Username: {username}',
      u'Database name: {database_name}',
      u'Query: {query}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{sequence_number}',
      u'{username}',
      u'{database_name}',
      u'{query}']


manager.FormattersManager.RegisterFormatter(PlsRecallFormatter)
