# -*- coding: utf-8 -*-
"""Formatter for the iPod device events."""

from plaso.formatters import interface
from plaso.formatters import manager


class IPodDeviceFormatter(interface.ConditionalEventFormatter):
  """Formatter for iPod device events."""

  DATA_TYPE = 'ipod:device:entry'

  FORMAT_STRING_PIECES = [
      u'Device ID: {device_id}',
      u'Type: {device_class}',
      u'[{family_id}]',
      u'Connected {use_count} times',
      u'Serial nr: {serial_number}',
      u'IMEI [{imei}]']

  SOURCE_LONG = 'iPod Connections'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(IPodDeviceFormatter)
