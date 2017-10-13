# -*- coding: utf-8 -*-
"""The syslog file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SyslogLineFormatter(interface.ConditionalEventFormatter):
  """Formatter for a syslog line event."""

  DATA_TYPE = 'syslog:line'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      '{severity} ',
      '[',
      '{reporter}',
      ', pid: {pid}',
      '] {body}']

  SOURCE_LONG = 'Log File'
  SOURCE_SHORT = 'LOG'


class SyslogCommentFormatter(interface.ConditionalEventFormatter):
  """Formatter for a syslog comment"""
  DATA_TYPE = 'syslog:comment'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = ['{body}']

  SOURCE_LONG = 'Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters(
    [SyslogLineFormatter, SyslogCommentFormatter])
