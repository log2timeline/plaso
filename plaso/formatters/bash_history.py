# -*- coding: utf-8 -*-
"""The Bash history formatter."""
from plaso.formatters import interface
from plaso.formatters import manager


class BashFormatter(interface.EventFormatter):
  """Formatter for Bash history events."""

  # Identifier for event data
  DATA_TYPE = u'bash:history:command'

  FORMAT_STRING = u'Command executed: {command}'
  FORMAT_STRING_SHORT = u'{command}'

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'Bash History'

manager.FormattersManager.RegisterFormatter(BashFormatter)
