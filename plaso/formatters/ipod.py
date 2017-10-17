# -*- coding: utf-8 -*-
"""The iPod device event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class IPodDeviceFormatter(interface.ConditionalEventFormatter):
  """Formatter for an iPod device event."""

  DATA_TYPE = 'ipod:device:entry'

  FORMAT_STRING_PIECES = [
      'Device ID: {device_id}',
      'Type: {device_class}',
      '[{family_id}]',
      'Connected {use_count} times',
      'Serial nr: {serial_number}',
      'IMEI [{imei}]']

  SOURCE_LONG = 'iPod Connections'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(IPodDeviceFormatter)
