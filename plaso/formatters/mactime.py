# -*- coding: utf-8 -*-
"""The Sleuthkit (TSK) bodyfile (or mactime) event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MactimeFormatter(interface.EventFormatter):
  """Formatter for a mactime event."""

  DATA_TYPE = 'fs:mactime:line'

  # The format string.
  FORMAT_STRING = '{filename}'

  SOURCE_LONG = 'Mactime Bodyfile'
  SOURCE_SHORT = 'FILE'


manager.FormattersManager.RegisterFormatter(MactimeFormatter)
