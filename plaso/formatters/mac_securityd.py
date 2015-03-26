# -*- coding: utf-8 -*-
"""The Mac OS X ASL securityd log file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacSecuritydLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for an ASL securityd log file event."""

  DATA_TYPE = 'mac:asl:securityd:line'

  FORMAT_STRING_PIECES = [
      u'Sender: {sender}',
      u'({sender_pid})',
      u'Level: {level}',
      u'Facility: {facility}',
      u'Text: {message}']

  FORMAT_STRING_SHORT_PIECES = [u'Text: {message}']

  SOURCE_LONG = 'Mac ASL Securityd Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacSecuritydLogFormatter)
