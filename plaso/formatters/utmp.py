# -*- coding: utf-8 -*-
"""The UTMP binary file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class UtmpSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for an UTMP session event."""

  DATA_TYPE = 'linux:utmp:event'

  FORMAT_STRING_PIECES = [
      'User: {user}',
      'Computer Name: {computer_name}',
      'Terminal: {terminal}',
      'PID: {pid}',
      'Terminal_ID: {terminal_id}',
      'Status: {status}',
      'IP Address: {ip_address}',
      'Exit: {exit}']

  FORMAT_STRING_SHORT_PIECES = ['User: {user}']

  SOURCE_LONG = 'UTMP session'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(UtmpSessionFormatter)
