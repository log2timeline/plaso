# -*- coding: utf-8 -*-
"""The syslog file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SyslogLineFormatter(interface.ConditionalEventFormatter):
  """Formatter for a syslog line event."""

  DATA_TYPE = u'syslog:line'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'[',
      u'{reporter}',
      u', pid: {pid}',
      u'] {body}']

  SOURCE_LONG = u'Log File'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(SyslogLineFormatter)
