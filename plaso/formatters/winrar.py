# -*- coding: utf-8 -*-
"""The WinRAR history event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinRARHistoryEventFormatter(interface.EventFormatter):
  """Formatter for a WinRAR history event."""

  DATA_TYPE = 'winrar:history'

  FORMAT_STRING = '[{key_path}] {entries}'
  FORMAT_STRING_ALTERNATIVE = '{entries}'

  SOURCE_LONG = 'Registry Key : WinRAR History'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(WinRARHistoryEventFormatter)
