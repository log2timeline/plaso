# -*- coding: utf-8 -*-
"""Windows Setupapi log event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SetupapiLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Setupapi log file event."""

  DATA_TYPE = 'setupapi:log:line'

  FORMAT_STRING_PIECES = [
      '{entry_type}',
      '{exit_status}']

  # Reversing fields for short description to prevent truncating the status
  FORMAT_STRING_SHORT_PIECES = [
      '{exit_status}',
      '{entry_type}']

  FORMAT_STRING_SEPARATOR = ' - '

  SOURCE_LONG = 'Windows Setupapi Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SetupapiLogFormatter)
