# -*- coding: utf-8 -*-
"""The Mac OS X securityd log file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacSecuritydLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a securityd log event."""

  DATA_TYPE = u'mac:securityd:line'

  FORMAT_STRING_PIECES = [
      u'Sender: {sender}',
      u'({sender_pid})',
      u'Level: {level}',
      u'Facility: {facility}',
      u'Text: {message}']

  FORMAT_STRING_SHORT_PIECES = [u'Text: {message}']

  SOURCE_LONG = u'Mac Securityd Log'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(MacSecuritydLogFormatter)
