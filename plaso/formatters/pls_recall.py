# -*- coding: utf-8 -*-
"""The PL/SQL Recall event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class PlsRecallFormatter(interface.ConditionalEventFormatter):
  """Formatter for a PL/SQL Recall file container event."""

  DATA_TYPE = 'PLSRecall:event'
  SOURCE_LONG = 'PL/SQL Developer Recall file'
  SOURCE_SHORT = 'PLSRecall'

  FORMAT_STRING_PIECES = [
      'Sequence number: {sequence_number}',
      'Username: {username}',
      'Database name: {database_name}',
      'Query: {query}']

  FORMAT_STRING_SHORT_PIECES = [
      '{sequence_number}',
      '{username}',
      '{database_name}',
      '{query}']


manager.FormattersManager.RegisterFormatter(PlsRecallFormatter)
