# -*- coding: utf-8 -*-
"""The Windows EventLog (EVT) file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinEVTFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows EventLog (EVT) record event."""

  DATA_TYPE = u'windows:evt:record'

  # TODO: add string representation of facility.
  FORMAT_STRING_PIECES = [
      u'[{event_identifier} /',
      u'0x{event_identifier:04x}]',
      u'Severity: {severity}',
      u'Record Number: {record_number}',
      u'Event Type: {event_type}',
      u'Event Category: {event_category}',
      u'Source Name: {source_name}',
      u'Computer Name: {computer_name}',
      u'Message string: {message_string}',
      u'Strings: {strings}']

  FORMAT_STRING_SHORT_PIECES = [
      u'[{event_identifier} /',
      u'0x{event_identifier:04x}]',
      u'Strings: {strings}']

  SOURCE_LONG = u'WinEVT'
  SOURCE_SHORT = u'EVT'

  # Mapping of the numeric event types to a descriptive string.
  _EVENT_TYPES = [
      u'Error event',
      u'Warning event',
      u'Information event',
      u'Success Audit event',
      u'Failure Audit event']

  _SEVERITY = [
      u'Success',
      u'Informational',
      u'Warning',
      u'Error']

  def GetEventTypeString(self, event_type):
    """Retrieves a string representation of the event type.

    Args:
      event_type: The numeric event type.

    Returns:
      An Unicode string containing a description of the event type.
    """
    if event_type >= 0 and event_type < len(self._EVENT_TYPES):
      return self._EVENT_TYPES[event_type]
    return u'Unknown {0:d}'.format(event_type)

  def GetSeverityString(self, severity):
    """Retrieves a string representation of the severity.

    Args:
      severity: The numeric severity.

    Returns:
      An Unicode string containing a description of the event type.
    """
    if severity >= 0 and severity < len(self._SEVERITY):
      return self._SEVERITY[severity]
    return u'Unknown {0:d}'.format(severity)

  def GetMessages(self, formatter_mediator, event_object):
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

    event_values = event_object.CopyToDict()

    event_type = event_values.get(u'event_type', None)
    if event_type is not None:
      event_values[u'event_type'] = self.GetEventTypeString(event_type)

    # TODO: add string representation of facility.

    severity = event_values.get(u'severity', None)
    if severity is not None:
      event_values[u'severity'] = self.GetSeverityString(severity)

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
          # Unable to create the message string.
          pass

    message_strings = []
    for string in strings:
      message_strings.append(u'\'{0:s}\''.format(string))
    message_string = u', '.join(message_strings)
    event_values[u'strings'] = u'[{0:s}]'.format(message_string)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinEVTFormatter)
