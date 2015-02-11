# -*- coding: utf-8 -*-
"""Formatter for the Windows events."""

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsVolumeCreationEventFormatter(interface.ConditionalEventFormatter):
  """Class that formats Windows volume creation events."""

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
