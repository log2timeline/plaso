# -*- coding: utf-8 -*-
"""The Bash history event formatter."""
from plaso.formatters import interface
from plaso.formatters import manager


class BashHistoryEventFormatter(interface.EventFormatter):
  """Formatter for Bash history events."""

  DATA_TYPE = u'bash:history:command'

  FORMAT_STRING = u'Command executed: {command}'
  FORMAT_STRING_SHORT = u'{command}'

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'Bash History'


manager.FormattersManager.RegisterFormatter(BashHistoryEventFormatter)
