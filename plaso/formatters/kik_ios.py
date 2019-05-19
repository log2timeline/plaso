# -*- coding: utf-8 -*-
"""The Kik kik.sqlite iOS database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors

class KikIOSMessageFormatter(interface.ConditionalEventFormatter):
  """Formatter for an iOS Kik message event."""

  DATA_TYPE = 'ios:kik:messaging'

  FORMAT_STRING_PIECES = [
      'Username: {username}',
      'Displayname: {displayname}',
      'Status: {message_status}',
      'Type: {message_type}',
      'Message: {body}']

  FORMAT_STRING_SHORT_PIECES = ['{body}']

  SOURCE_LONG = 'Kik iOS messages'
  SOURCE_SHORT = 'Kik iOS'

  _MESSAGE_TYPE = {
      1: 'received',
      2: 'sent',
      3: 'message to group admin',
      4: 'message to group'
  }

  _MESSAGE_STATUS = {
      0: 'unread',
      2: 'message not sent',
      6: 'sent to Kik server',
      14: 'delivered ',
      16: 'message read',
      30: 'read after immediate delivery',
      38: 'not a member of the group',
      66: 'delay in reaching Kik server',
      70: 'push notification sent',
      78: 'delivered after offline',
      94: 'read after offline'
  }

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

    message_type = event_values.get('message_type', None)
    if message_type is not None:
      event_values['message_type'] = (
          self._MESSAGE_TYPE.get(message_type, 'UNKNOWN'))

    message_status = event_values.get('message_status', None)
    if message_status is not None:
      event_values['message_status'] = (
          self._MESSAGE_STATUS.get(message_status, 'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(KikIOSMessageFormatter)
