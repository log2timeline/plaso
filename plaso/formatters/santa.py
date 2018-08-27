# -*- coding: utf-8 -*-
"""Santa log file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SantaExecutionFormatter(interface.ConditionalEventFormatter):
  """Formatter for a santa execution event."""

  DATA_TYPE = 'santa:execution'

  FORMAT_STRING_PIECES = [
      'Santa {decision}',
      'process: {process_path}',
      'hash: {process_hash}'
  ]

  FORMAT_STRING_SHORT_PIECES = [
      '{decision}',
      'process: {process_path}'
  ]

  SOURCE_LONG = 'Santa Execution'
  SOURCE_SHORT = 'LOG'


class SantaFileSystemFormatter(interface.ConditionalEventFormatter):
  """Formatter for a santa file system event."""

  DATA_TYPE = 'santa:file_system_event'

  FORMAT_STRING_PIECES = [
      'Santa {action} event',
      '{file_path}',
      'by process: {process_path}'
  ]

  FORMAT_STRING_SHORT_PIECES = [
      'File {action}',
      'on: {file_path}'
  ]

  SOURCE_LONG = 'Santa FSEvent'
  SOURCE_SHORT = 'LOG'


class SantaDiskMountsFormatter(interface.ConditionalEventFormatter):
  """Formatter for a santa disk mount event."""

  DATA_TYPE = 'santa:diskmount'

  FORMAT_STRING_PIECES = [
      'Santa {action}',
      'on ({mount})',
      'serial: ({serial})',
      'for ({dmg_path})'
  ]

  FORMAT_STRING_SHORT_PIECES = [
      '{action}',
      '{volume}'
  ]

  SOURCE_LONG = 'Santa disk mount'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters(
    [SantaExecutionFormatter, SantaFileSystemFormatter,
     SantaDiskMountsFormatter])
