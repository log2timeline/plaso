# -*- coding: utf-8 -*-
"""The Sleuthkit (TSK) bodyfile (or mactime) event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class MactimeFormatter(interface.EventFormatter):
  """Formatter for a mactime event."""

  DATA_TYPE = u'fs:mactime:line'

  # The format string.
  FORMAT_STRING = u'{filename}'

  SOURCE_LONG = u'Mactime Bodyfile'
  SOURCE_SHORT = u'FILE'


manager.FormattersManager.RegisterFormatter(MactimeFormatter)
