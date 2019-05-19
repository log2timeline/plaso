# -*- coding: utf-8 -*-
"""Tango on Android databases formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class TangoAndroidMessageFormatter(interface.ConditionalEventFormatter):
  """Tango on Android message event formatter."""

  DATA_TYPE = 'tango:android:message'

  FORMAT_STRING_PIECES = [
      '{direction}',
      'Message ({message_identifier})',
  ]

  FORMAT_STRING_SHORT_PIECES = [
      '{direction}',
      'Message ({message_identifier})'
  ]

  SOURCE_LONG = 'Tango Android Message'
  SOURCE_SHORT = 'Tango Android'

  _DIRECTION = {
      1: 'Incoming',
      2: 'Outgoing'
  }

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event_data (EventData): event data.

    Returns:
      tuple[str, str]: formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    direction = event_values.get('direction', None)
    if direction is not None:
      event_values['direction'] = self._DIRECTION.get(direction, 'Unknown')

    return self._ConditionalFormatMessages(event_values)


class TangoAndroidConversationFormatter(interface.ConditionalEventFormatter):
  """Tango on Android conversation event formatter."""

  DATA_TYPE = 'tango:android:conversation'

  FORMAT_STRING_PIECES = [
      'Conversation ({conversation_identifier})',
  ]

  FORMAT_STRING_SHORT_PIECES = [
      'Conversation ({conversation_identifier})',
  ]

  SOURCE_LONG = 'Tango Android Conversation'
  SOURCE_SHORT = 'Tango Android'


class TangoAndroidContactFormatter(interface.ConditionalEventFormatter):
  """Tango on Android contact event formatter."""

  DATA_TYPE = 'tango:android:contact'

  FORMAT_STRING_PIECES = [
      '{first_name}',
      '{last_name}',
      '{gender}',
      'birthday: {birthday}',
      'Status: {status}',
      'Friend: {is_friend}',
      'Request type: {friend_request_type}',
      'Request message: {friend_request_message}'
  ]

  FORMAT_STRING_SHORT_PIECES = [
      '{first_name}',
      '{last_name}',
      'Status: {status}'
  ]

  SOURCE_LONG = 'Tango Android Contact'
  SOURCE_SHORT = 'Tango Android'

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event_data (EventData): event data.

    Returns:
      tuple[str, str]: formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    is_friend = event_values.get('is_friend', None)
    if is_friend is not None:
      event_values['is_friend'] = '{0!s}'.format(is_friend)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    TangoAndroidMessageFormatter, TangoAndroidConversationFormatter,
    TangoAndroidContactFormatter])
