# -*- coding: utf-8 -*-
"""The Basic Security Module (BSM) binary files event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors
from plaso.unix import bsmtoken


class BSMFormatter(interface.ConditionalEventFormatter):
  """Formatter for a BSM log entry."""

  DATA_TYPE = 'bsm:event'

  FORMAT_STRING_PIECES = [
      'Type: {event_type_string}',
      '({event_type})',
      'Return: {return_value}',
      'Information: {extra_tokens}']

  FORMAT_STRING_SHORT_PIECES = [
      'Type: {event_type}',
      'Return: {return_value}']

  SOURCE_LONG = 'BSM entry'
  SOURCE_SHORT = 'LOG'

  # pylint: disable=unused-argument
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

    event_type = event_values.get('event_type', None)
    if event_type:
      event_values['event_type_string'] = bsmtoken.BSM_AUDIT_EVENT.get(
          event_type, 'UNKNOWN')

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(BSMFormatter)
