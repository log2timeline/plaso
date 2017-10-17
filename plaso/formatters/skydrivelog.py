# -*- coding: utf-8 -*-
"""The SkyDrive log event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SkyDriveLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SkyDrive log file event."""

  DATA_TYPE = 'skydrive:log:line'

  FORMAT_STRING_PIECES = [
      '[{module}',
      '{source_code}',
      '{log_level}]',
      '{detail}']

  FORMAT_STRING_SHORT_PIECES = ['{detail}']

  SOURCE_LONG = 'SkyDrive Log File'
  SOURCE_SHORT = 'LOG'


class SkyDriveOldLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SkyDrive old log file event."""

  DATA_TYPE = 'skydrive:log:old:line'

  FORMAT_STRING_PIECES = [
      '[{source_code}]',
      '({log_level})',
      '{text}']

  FORMAT_STRING_SHORT_PIECES = ['{text}']

  SOURCE_LONG = 'SkyDrive Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    SkyDriveLogFormatter, SkyDriveOldLogFormatter])
