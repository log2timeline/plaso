# -*- coding: utf-8 -*-
"""The MacOS wifi.log file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacWifiLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a wifi.log file event."""

  DATA_TYPE = 'mac:wifilog:line'

  FORMAT_STRING_PIECES = [
      'Action: {action}',
      'Agent: {agent}',
      '({function})',
      'Log: {text}']

  FORMAT_STRING_SHORT_PIECES = [
      'Action: {action}']

  SOURCE_LONG = 'Mac Wifi Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacWifiLogFormatter)
