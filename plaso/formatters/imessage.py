# -*- coding: utf-8 -*-
"""The iMessage chat.db (OSX) and sms.db (iOS)database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class IMessageFormatter(interface.ConditionalEventFormatter):
  """Formatter for an iMessage and SMS event."""

  DATA_TYPE = 'imessage:event:chat'

  FORMAT_STRING_PIECES = [
      'Row ID: {identifier}',
      'iMessage ID: {imessage_id}',
      'Read Receipt: {read_receipt}',
      'Message Type: {message_type}',
      'Service: {service}',
      'Attachment Location: {attachment_location}',
      'Message Content: {text}']

  FORMAT_STRING_SHORT_PIECES = ['{text}']

  SOURCE_LONG = 'Apple iMessage Application'
  SOURCE_SHORT = 'iMessage'

  _READ_RECEIPT = {
      0: False,
      1: True
  }
  _MESSAGE_TYPE = {
      0: 'Received',
      1: 'Sent'
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

    read_receipt = event_values.get('read_receipt', None)
    if read_receipt is not None:
      event_values['read_receipt'] = (
          self._READ_RECEIPT.get(read_receipt, 'UNKNOWN'))

    message_type = event_values.get('message_type', None)
    if message_type is not None:
      event_values['message_type'] = (
          self._MESSAGE_TYPE.get(message_type, 'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(IMessageFormatter)
