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
      '[{exit_status}',
      '{end_time}]']

  FORMAT_STRING_SHORT_PIECES = ['{entry_type}']

  SOURCE_LONG = 'Windows Setupapi Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SetupapiLogFormatter)
