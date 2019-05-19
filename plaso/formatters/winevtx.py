# -*- coding: utf-8 -*-
"""The Windows XML EventLog (EVTX) file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinEVTXFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows XML EventLog (EVTX) record event."""

  DATA_TYPE = 'windows:evtx:record'

  FORMAT_STRING_PIECES = [
      '[{event_identifier} /',
      '0x{event_identifier:04x}]',
      'Source Name: {source_name}',
      'Message string: {message_string}',
      'Strings: {strings}',
      'Computer Name: {computer_name}',
      'Record Number: {record_number}',
      'Event Level: {event_level}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{event_identifier} /',
      '0x{event_identifier:04x}]',
      'Strings: {strings}']

  SOURCE_LONG = 'WinEVTX'
  SOURCE_SHORT = 'EVT'

  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
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

    source_name = event_values.get('source_name', None)
    message_identifier = event_values.get('message_identifier', None)
    strings = event_values.get('strings', [])
    if source_name and message_identifier:
      message_string = formatter_mediator.GetWindowsEventMessage(
          source_name, message_identifier)
      if message_string:
        try:
          event_values['message_string'] = message_string.format(*strings)
        except IndexError:
          pass

    message_strings = []
    for string in strings:
      if string:
        message_strings.append('\'{0:s}\''.format(string))
    message_string = ', '.join(message_strings)
    event_values['strings'] = '[{0:s}]'.format(message_string)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinEVTXFormatter)
