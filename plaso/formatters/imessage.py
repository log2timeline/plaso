# -*- coding: utf-8 -*-
"""The iMessage chat.db (OSX) and sms.db (iOS)database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class IMessageFormatter(interface.ConditionalEventFormatter):
  """Formatter for an iMessage and SMS event."""

  DATA_TYPE = u'imessage:event:chat'

  FORMAT_STRING_PIECES = [
      u'Row ID: {identifier}',
      u'iMessage ID: {imessage_id}',
      u'Read Receipt: {read_receipt}',
      u'Message Type: {message_type}',
      u'Service: {service}',
      u'Attachment Location: {attachment_location}',
      u'Message Content: {text}']

  FORMAT_STRING_SHORT_PIECES = [u'{text}']

  SOURCE_LONG = u'Apple iMessage Application'
  SOURCE_SHORT = u'iMessage'

  _READ_RECEIPT = {
      0: False,
      1: True
  }
  _MESSAGE_TYPE = {
      0: u'Received',
      1: u'Sent'
  }

  def GetMessages(self, unused_formatter_mediator, event):
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

    read_receipt = event_values.get(u'read_receipt', None)
    if read_receipt is not None:
      event_values[u'read_receipt'] = (
          self._READ_RECEIPT.get(read_receipt, u'UNKNOWN'))

    message_type = event_values.get(u'message_type', None)
    if message_type is not None:
      event_values[u'message_type'] = (
          self._MESSAGE_TYPE.get(message_type, u'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(IMessageFormatter)
