# -*- coding: utf-8 -*-
"""The Mac OS X securityd log file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacSecuritydLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a securityd log event."""

  DATA_TYPE = 'mac:securityd:line'

  FORMAT_STRING_PIECES = [
      'Sender: {sender}',
      '({sender_pid})',
      'Level: {level}',
      'Facility: {facility}',
      'Text: {message}']

  FORMAT_STRING_SHORT_PIECES = ['Text: {message}']

  SOURCE_LONG = 'Mac Securityd Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacSecuritydLogFormatter)
