# -*- coding: utf-8 -*-
"""The Google Hangouts messages database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class HangoutsFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Hangouts message event."""

  DATA_TYPE = 'android:messaging:hangouts'

  FORMAT_STRING_PIECES = [
      'Sender: {sender}',
      'Body: {body}',
      'Status: {message_status}',
      'Type: {message_type}']

  FORMAT_STRING_SHORT_PIECES = ['{body}']

  SOURCE_LONG = 'Google Hangouts Message'
  SOURCE_SHORT = 'HANGOUTS'

  _MESSAGE_STATUSES = {
      0: 'UNREAD',
      4: 'READ'}

  _MESSAGE_TYPES = {
      1: 'SENT',
      2: 'RECEIVED'}

  def __init__(self):
    """Initializes a Hangouts message event format helper."""
    super(HangoutsFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='message_status',
        output_attribute='message_status', values=self._MESSAGE_STATUSES)

    self.helpers.append(helper)

    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='message_type',
        output_attribute='message_type', values=self._MESSAGE_TYPES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(HangoutsFormatter)
