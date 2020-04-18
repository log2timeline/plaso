# -*- coding: utf-8 -*-
"""The Kik kik.sqlite iOS database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


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

  _MESSAGE_TYPES = {
      1: 'received',
      2: 'sent',
      3: 'message to group admin',
      4: 'message to group'
  }

  _MESSAGE_STATUSES = {
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

  def __init__(self):
    """Initializes an iOS Kik message event format helper."""
    super(KikIOSMessageFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='message_status',
        output_attribute='message_status', values=self._MESSAGE_STATUSES)

    self.helpers.append(helper)

    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='message_type',
        output_attribute='message_type', values=self._MESSAGE_TYPES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(KikIOSMessageFormatter)
