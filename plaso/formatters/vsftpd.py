# -*- coding: utf-8 -*-
"""The vsftpd log file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class VsftpdLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a vsftpd log event data."""

  DATA_TYPE = 'vsftpd:log'

  FORMAT_STRING_PIECES = [
      '{text}']

  SOURCE_LONG = 'vsftpd log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(VsftpdLogFormatter)
