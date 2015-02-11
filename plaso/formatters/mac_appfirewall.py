# -*- coding: utf-8 -*-
"""Formatter for the Mac appfirewall.log file."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacAppFirewallLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for Mac appfirewall.log file."""

  DATA_TYPE = 'mac:asl:appfirewall:line'

  FORMAT_STRING_PIECES = [
      u'Computer: {computer_name}',
      u'Agent: {agent}',
      u'Status: {status}',
      u'Process name: {process_name}',
      u'Log: {action}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Process name: {process_name}',
      u'Status: {status}']

  SOURCE_LONG = 'Mac AppFirewall Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacAppFirewallLogFormatter)
