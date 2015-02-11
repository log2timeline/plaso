# -*- coding: utf-8 -*-
"""Formatter for ASL securityd log file."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacSecuritydLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for ASL Securityd file."""

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
