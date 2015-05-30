# -*- coding: utf-8 -*-
"""The UTMP binary file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class UtmpSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for an UTMP session event."""

  DATA_TYPE = u'linux:utmp:event'

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

  SOURCE_LONG = u'UTMP session'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(UtmpSessionFormatter)
