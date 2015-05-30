# -*- coding: utf-8 -*-
"""The iPod device event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class IPodDeviceFormatter(interface.ConditionalEventFormatter):
  """Formatter for an iPod device event."""

  DATA_TYPE = u'ipod:device:entry'

  FORMAT_STRING_PIECES = [
      u'Device ID: {device_id}',
      u'Type: {device_class}',
      u'[{family_id}]',
      u'Connected {use_count} times',
      u'Serial nr: {serial_number}',
      u'IMEI [{imei}]']

  SOURCE_LONG = u'iPod Connections'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(IPodDeviceFormatter)
