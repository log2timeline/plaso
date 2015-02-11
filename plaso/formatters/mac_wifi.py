# -*- coding: utf-8 -*-
"""Formatter for Mac wifi.log file."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacWifiLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for Mac Wifi file."""

  DATA_TYPE = 'mac:wifilog:line'

  FORMAT_STRING_PIECES = [
      u'Action: {action}',
      u'Agent: {user}',
      u'({function})',
      u'Log: {text}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Action: {action}']

  SOURCE_LONG = 'Mac Wifi Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(MacWifiLogFormatter)
