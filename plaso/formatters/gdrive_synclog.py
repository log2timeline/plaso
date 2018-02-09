# -*- coding: utf-8 -*-
"""Google Drive Sync log event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class GoogleDriveSyncLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Drive Sync log file event."""

  DATA_TYPE = 'gdrive_sync:log:line'

  FORMAT_STRING_PIECES = [
      '[{log_level}',
      '{pid}',
      '{thread}',
      '{source_code}]',
      '{message}']

  FORMAT_STRING_SHORT_PIECES = ['{message}']

  SOURCE_LONG = 'GoogleDriveSync Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(GoogleDriveSyncLogFormatter)
