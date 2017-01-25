# -*- coding: utf-8 -*-
"""The Mac OS X wifi.log file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacWifiLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a wifi.log file event."""

  DATA_TYPE = u'mac:wifilog:line'

  FORMAT_STRING_PIECES = [
      u'Log: {body}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Log: {body}']

  SOURCE_LONG = u'Mac Wifi Log'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(MacWifiLogFormatter)
