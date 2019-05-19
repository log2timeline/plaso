# -*- coding: utf-8 -*-
"""The Google Hangouts messages database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


_MESSAGE_TYPES = {
    1: 'SENT',
    2: 'RECEIVED'}

_MESSAGE_STATUSES = {
    0: 'UNREAD',
    4: 'READ'}


class HangoutsFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Hangouts message event."""

  DATA_TYPE = 'android:messaging:hangouts'

  FORMAT_STRING_PIECES = [
      'Sender: {sender}',
      'Body: {body}',
      'Status: {message_status}',
      'Type: {message_type}']

  FORMAT_STRING_SHORT_PIECES = ['{body}']

  SOURCE_LONG = 'Google Hangouts Message'
  SOURCE_SHORT = 'HANGOUTS'

  # VALUE_FORMATTERS contains formatting functions for event values that are
  # not ready for human consumption.
  # These functions replace the integer codes for scan types and scan results
  # (a.k.a. actions) with human-readable strings.
  VALUE_FORMATTERS = {
      'message_type': lambda message_type: _MESSAGE_TYPES[message_type],
      'message_status':
          lambda message_status: _MESSAGE_STATUSES[message_status]}

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    If any event values have a matching formatting function in VALUE_FORMATTERS,
    they are run through that function; then the dictionary is passed to the
    superclass's formatting method.

    Args:
      formatter_mediator (FormatterMediator): not used.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter(
          'Unsupported data type: {0:s}.'.format(event_data.data_type))

    event_values = event_data.CopyToDict()
    for formattable_value_name, formatter in self.VALUE_FORMATTERS.items():
      if formattable_value_name in event_values:
        value = event_values[formattable_value_name]
        event_values[formattable_value_name] = formatter(value)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(HangoutsFormatter)
