# -*- coding: utf-8 -*-
"""Google Drive Sync log event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class GDriveSyncLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Drive Sync log file event."""

  DATA_TYPE = 'gdrive_sync:log:line'

  FORMAT_STRING_PIECES = [
      '[{log_level}',
      '{pid}',
      '{thread}',
      '{source_code}]',
      '{message}']

  FORMAT_STRING_SHORT_PIECES = ['{message}']

  SOURCE_LONG = 'GDriveSync Log File'
  SOURCE_SHORT = 'LOG'

  # TODO: do we want a GetMessages method here? Current iteration has some
  # leading whitespace/other hairiness that makes it clunky to compare test
  # cases, but I don't know what the expectations are for where/how to clean
  # those up -- might be I have a poorly-implemented pyparsing structure.


manager.FormattersManager.RegisterFormatter(GDriveSyncLogFormatter)
