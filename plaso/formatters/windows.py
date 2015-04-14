# -*- coding: utf-8 -*-
"""The Windows event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsVolumeCreationEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows volume creation event."""

  DATA_TYPE = 'windows:volume:creation'

  FORMAT_STRING_PIECES = [
      u'{device_path}',
      u'Serial number: 0x{serial_number:08X}',
      u'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{device_path}',
      u'Origin: {origin}']

  SOURCE_LONG = 'System'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(WindowsVolumeCreationEventFormatter)
