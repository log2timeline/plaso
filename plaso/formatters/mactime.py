# -*- coding: utf-8 -*-
"""Formatter for the Sleuthkit (TSK) bodyfile or mactime format."""

from plaso.formatters import interface
from plaso.formatters import manager


class MactimeFormatter(interface.EventFormatter):
  """Class that formats mactime bodyfile events."""

  DATA_TYPE = 'fs:mactime:line'

  # The format string.
  FORMAT_STRING = u'{filename}'

  SOURCE_LONG = 'Mactime Bodyfile'
  SOURCE_SHORT = 'FILE'


manager.FormattersManager.RegisterFormatter(MactimeFormatter)
