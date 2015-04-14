# -*- coding: utf-8 -*-
"""The UTMPX binary file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class UtmpxSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for an UTMPX session event."""

  DATA_TYPE = 'mac:utmpx:event'

  FORMAT_STRING_PIECES = [
      u'User: {user}',
      u'Status: {status}',
      u'Computer Name: {computer_name}',
      u'Terminal: {terminal}']

  FORMAT_STRING_SHORT_PIECES = [u'User: {user}']

  SOURCE_LONG = 'UTMPX session'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(UtmpxSessionFormatter)
