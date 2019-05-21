# -*- coding: utf-8 -*-
"""The Windows Recycler/Recycle Bin formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


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

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    drive_number = event_values.get('drive_number', None)
    event_values['drive_letter'] = self._DRIVE_LETTER.get(
        drive_number, 'UNKNOWN')

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinRecyclerFormatter)
