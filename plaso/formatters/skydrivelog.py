# -*- coding: utf-8 -*-
"""This file contains a skydrivelog formatter in plaso."""

from plaso.formatters import interface
from plaso.formatters import manager


class SkyDriveLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for SkyDrive log files events."""

  DATA_TYPE = 'skydrive:log:line'

  FORMAT_STRING_PIECES = [
      u'[{source_code}]',
      u'({log_level})',
      u'{text}']

  FORMAT_STRING_SHORT_PIECES = [u'{text}']

  SOURCE_LONG = 'SkyDrive Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SkyDriveLogFormatter)
