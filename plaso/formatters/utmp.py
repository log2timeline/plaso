# -*- coding: utf-8 -*-
"""Formatter for the UTMP binary files."""

from plaso.formatters import interface
from plaso.formatters import manager


class UtmpSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for UTMP session."""

  DATA_TYPE = 'linux:utmp:event'

  FORMAT_STRING_PIECES = [
      u'User: {user}',
      u'Computer Name: {computer_name}',
      u'Terminal: {terminal}',
      u'PID: {pid}',
      u'Terminal_ID: {terminal_id}',
      u'Status: {status}',
      u'IP Address: {ip_address}',
      u'Exit: {exit}']

  FORMAT_STRING_SHORT_PIECES = [u'User: {user}']

  SOURCE_LONG = 'UTMP session'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(UtmpSessionFormatter)
