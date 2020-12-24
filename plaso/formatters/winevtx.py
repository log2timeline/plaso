# -*- coding: utf-8 -*-
"""The Windows XML EventLog (EVTX) file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


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

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    message_strings = []
    for string in event_values.get('strings', []):
      if string:
        message_strings.append('\'{0:s}\''.format(string))
    message_string = ', '.join(message_strings)
    event_values['strings'] = '[{0:s}]'.format(message_string)


manager.FormattersManager.RegisterFormatter(WinEVTXFormatter)
