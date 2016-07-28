# -*- coding: utf-8 -*-
"""The Windows XML EventLog (EVTX) file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinEVTXFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows XML EventLog (EVTX) record event."""

  DATA_TYPE = u'windows:evtx:record'

  FORMAT_STRING_PIECES = [
      u'[{event_identifier} /',
      u'0x{event_identifier:04x}]',
      u'Record Number: {record_number}',
      u'Event Level: {event_level}',
      u'Source Name: {source_name}',
      u'Computer Name: {computer_name}',
      u'Message string: {message_string}',
      u'Strings: {strings}']

  FORMAT_STRING_SHORT_PIECES = [
      u'[{event_identifier} /',
      u'0x{event_identifier:04x}]',
      u'Strings: {strings}']

  SOURCE_LONG = u'WinEVTX'
  SOURCE_SHORT = u'EVT'

  def GetMessages(self, formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    source_name = event_values.get(u'source_name', None)
    message_identifier = event_values.get(u'message_identifier', None)
    strings = event_values.get(u'strings', [])
    if source_name and message_identifier:
      message_string = formatter_mediator.GetWindowsEventMessage(
          source_name, message_identifier)
      if message_string:
        try:
          event_values[u'message_string'] = message_string.format(*strings)
        except IndexError:
          pass

    message_strings = []
    for string in strings:
      message_strings.append(u'\'{0:s}\''.format(string))
    message_string = u', '.join(message_strings)
    event_values[u'strings'] = u'[{0:s}]'.format(message_string)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinEVTXFormatter)
