# -*- coding: utf-8 -*-
"""The SkyDrive log event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SkyDriveLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SkyDrive log file event."""

  DATA_TYPE = u'skydrive:log:line'

  FORMAT_STRING_PIECES = [
      u'[{module}',
      u'{source_code}',
      u'{log_level}]',
      u'{detail}']

  FORMAT_STRING_SHORT_PIECES = [u'{detail}']

  SOURCE_LONG = u'SkyDrive Log File'
  SOURCE_SHORT = u'LOG'


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


manager.FormattersManager.RegisterFormatters([
    SkyDriveLogFormatter, SkyDriveOldLogFormatter])
