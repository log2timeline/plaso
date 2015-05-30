# -*- coding: utf-8 -*-
"""The Windows Recycler/Recycle Bin formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinRecyclerFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Recycler/Recycle Bin file event."""

  DATA_TYPE = u'windows:metadata:deleted_item'

  _DRIVE_LETTER = {
      0x00: u'A',
      0x01: u'B',
      0x02: u'C',
      0x03: u'D',
      0x04: u'E',
      0x05: u'F',
      0x06: u'G',
      0x07: u'H',
      0x08: u'I',
      0x09: u'J',
      0x0A: u'K',
      0x0B: u'L',
      0x0C: u'M',
      0x0D: u'N',
      0x0E: u'O',
      0x0F: u'P',
      0x10: u'Q',
      0x11: u'R',
      0x12: u'S',
      0x13: u'T',
      0x14: u'U',
      0x15: u'V',
      0x16: u'W',
      0x17: u'X',
      0x18: u'Y',
      0x19: u'Z',
  }

  # The format string.
  FORMAT_STRING_PIECES = [
      u'DC{index} ->',
      u'{orig_filename}',
      u'[{short_filename}]',
      u'(from drive: {drive_letter})']

  FORMAT_STRING_SHORT_PIECES = [
      u'Deleted file: {orig_filename}']

  SOURCE_LONG = u'Recycle Bin'
  SOURCE_SHORT = u'RECBIN'

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.GetValues()

    drive_number = event_values.get(u'drive_number', None)
    event_values[u'drive_letter'] = self._DRIVE_LETTER.get(
        drive_number, u'UNKNOWN')

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinRecyclerFormatter)
