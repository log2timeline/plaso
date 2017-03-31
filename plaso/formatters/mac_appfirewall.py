# -*- coding: utf-8 -*-
"""The Mac OS X appfirewall.log file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacAppFirewallLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for Mac OS X appfirewall.log file event."""

  DATA_TYPE = u'mac:appfirewall:line'

  FORMAT_STRING_PIECES = [
      u'Computer: {computer_name}',
      u'Agent: {agent}',
      u'Status: {status}',
      u'Process name: {process_name}',
      u'Log: {action}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Process name: {process_name}',
      u'Status: {status}']

  SOURCE_LONG = u'Mac AppFirewall Log'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(MacAppFirewallLogFormatter)
