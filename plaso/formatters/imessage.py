# -*- coding: utf-8 -*-
"""The iMessage chat.db (OSX) and sms.db (iOS)database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class IMessageFormatter(interface.ConditionalEventFormatter):
  """Formatter for an iMessage chat event."""

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

  _READ_RECEIPTS = {
      0: False,
      1: True
  }
  _MESSAGE_TYPES = {
      0: 'Received',
      1: 'Sent'
  }

  def __init__(self):
    """Initializes an iMessage chat event format helper."""
    super(IMessageFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='message_type',
        output_attribute='message_type', values=self._MESSAGE_TYPES)

    self.helpers.append(helper)

    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='read_receipt',
        output_attribute='read_receipt', values=self._READ_RECEIPTS)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(IMessageFormatter)
