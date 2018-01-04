# -*- coding: utf-8 -*-
"""The MacOS appfirewall.log file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacAppFirewallLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for MacOS appfirewall.log file event."""

  DATA_TYPE = 'mac:appfirewall:line'

  FORMAT_STRING_PIECES = [
      'Computer: {computer_name}',
      'Agent: {agent}',
      'Status: {status}',
      'Process name: {process_name}',
      'Log: {action}']

  FORMAT_STRING_SHORT_PIECES = [
      'Process name: {process_name}',
      'Status: {status}']

  SOURCE_LONG = 'Mac AppFirewall Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacAppFirewallLogFormatter)
