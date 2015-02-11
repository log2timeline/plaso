# -*- coding: utf-8 -*-
"""This file contains a syslog formatter in plaso."""

from plaso.formatters import interface
from plaso.formatters import manager


class SyslogLineFormatter(interface.ConditionalEventFormatter):
  """Formatter for syslog files."""

  DATA_TYPE = 'syslog:line'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'[',
      u'{reporter}',
      u', pid: {pid}',
      u'] {body}']

  SOURCE_LONG = 'Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SyslogLineFormatter)
