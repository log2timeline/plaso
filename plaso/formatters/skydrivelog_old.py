# -*- coding: utf-8 -*-
"""The SkyDrive old log event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SkyDriveOldLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SkyDrive old log file event."""

  DATA_TYPE = u'skydrive:log:old:line'

  FORMAT_STRING_PIECES = [
      u'[{source_code}]',
      u'({log_level})',
      u'{text}']

  FORMAT_STRING_SHORT_PIECES = [u'{text}']

  SOURCE_LONG = u'SkyDrive Log File'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(SkyDriveOldLogFormatter)
