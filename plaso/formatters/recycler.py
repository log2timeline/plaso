# -*- coding: utf-8 -*-
"""The Windows Recycler/Recycle Bin formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinRecyclerFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Recycler/Recycle Bin file event."""

  DATA_TYPE = 'windows:metadata:deleted_item'

  _DRIVE_LETTER = {
      0x00: 'A',
      0x01: 'B',
      0x02: 'C',
      0x03: 'D',
      0x04: 'E',
      0x05: 'F',
      0x06: 'G',
      0x07: 'H',
      0x08: 'I',
      0x09: 'J',
      0x0A: 'K',
      0x0B: 'L',
      0x0C: 'M',
      0x0D: 'N',
      0x0E: 'O',
      0x0F: 'P',
      0x10: 'Q',
      0x11: 'R',
      0x12: 'S',
      0x13: 'T',
      0x14: 'U',
      0x15: 'V',
      0x16: 'W',
      0x17: 'X',
      0x18: 'Y',
      0x19: 'Z',
  }

  # The format string.
  FORMAT_STRING_PIECES = [
      'DC{record_index} ->',
      '{original_filename}',
      '[{short_filename}]',
      '(from drive: {drive_letter})']

  FORMAT_STRING_SHORT_PIECES = [
      'Deleted file: {original_filename}']

  SOURCE_LONG = 'Recycle Bin'
  SOURCE_SHORT = 'RECBIN'

  def __init__(self):
    """Initializes a Windows Recycler/Recycle Bin file event format helper."""
    super(WinRecyclerFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='drive_number',
        output_attribute='drive_letter', values=self._DRIVE_LETTER)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(WinRecyclerFormatter)
