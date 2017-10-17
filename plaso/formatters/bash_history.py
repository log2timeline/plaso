# -*- coding: utf-8 -*-
"""The Bash history event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class BashHistoryEventFormatter(interface.EventFormatter):
  """Formatter for Bash history events."""

  DATA_TYPE = 'bash:history:command'

  FORMAT_STRING = 'Command executed: {command}'
  FORMAT_STRING_SHORT = '{command}'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Bash History'


manager.FormattersManager.RegisterFormatter(BashHistoryEventFormatter)
