# -*- coding: utf-8 -*-
"""The Windows EventLog (EVT) file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinEVTFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows EventLog (EVT) record event."""

  DATA_TYPE = 'windows:evt:record'

  # TODO: add string representation of facility.
  FORMAT_STRING_PIECES = [
      '[{event_identifier} /',
      '0x{event_identifier:04x}]',
      'Source Name: {source_name}',
      'Message string: {message_string}',
      'Strings: {strings}',
      'Computer Name: {computer_name}',
      'Severity: {severity}',
      'Record Number: {record_number}',
      'Event Type: {event_type}',
      'Event Category: {event_category}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{event_identifier} /',
      '0x{event_identifier:04x}]',
      'Strings: {strings}']

  # Mapping of the numeric event types to a descriptive string.
  _EVENT_TYPES = [
      'Error event',
      'Warning event',
      'Information event',
      'Success Audit event',
      'Failure Audit event']

  _SEVERITY = [
      'Success',
      'Informational',
      'Warning',
      'Error']

  def GetEventTypeString(self, event_type):
    """Retrieves a string representation of the event type.

    Args:
      event_type (int): event type.

    Returns:
      str: description of the event type.
    """
    if 0 <= event_type < len(self._EVENT_TYPES):
      return self._EVENT_TYPES[event_type]
    return 'Unknown {0:d}'.format(event_type)

  def GetSeverityString(self, severity):
    """Retrieves a string representation of the severity.

    Args:
      severity (int): severity.

    Returns:
      str: description of the event severity.
    """
    if 0 <= severity < len(self._SEVERITY):
      return self._SEVERITY[severity]
    return 'Unknown {0:d}'.format(severity)

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    event_type = event_values.get('event_type', None)
    if event_type is not None:
      event_values['event_type'] = self.GetEventTypeString(event_type)

    # TODO: add string representation of facility.

    severity = event_values.get('severity', None)
    if severity is not None:
      event_values['severity'] = self.GetSeverityString(severity)

    message_strings = []
    for string in event_values.get('strings', []):
      message_strings.append('\'{0:s}\''.format(string))
    message_string = ', '.join(message_strings)
    event_values['strings'] = '[{0:s}]'.format(message_string)


manager.FormattersManager.RegisterFormatter(WinEVTFormatter)
