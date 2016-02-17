# -*- coding: utf-8 -*-
"""The Kik kik.sqlite iOS database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors

class KikIOSMessageFormatter(interface.ConditionalEventFormatter):
  """Formatter for an iOS Kik message event."""

  DATA_TYPE = u'ios:kik:messaging'

  FORMAT_STRING_PIECES = [
      u'Username: {username}',
      u'Displayname: {displayname}',
      u'Status: {message_status}',
      u'Type: {message_type}',
      u'Message: {body}']

  FORMAT_STRING_SHORT_PIECES = [u'{body}']

  SOURCE_LONG = u'Kik iOS messages'
  SOURCE_SHORT = u'Kik iOS'

  _MESSAGE_TYPE = {
      1: u'received',
      2: u'sent',
      3: u'message to group admin',
      4: u'message to group'
  }

  _MESSAGE_STATUS = {
      0: u'unread',
      2: u'message not sent',
      6: u'sent to Kik server',
      14: u'delivered ',
      16: u'message read',
      30: u'read after immediate delivery',
      38: u'not a member of the group',
      66: u'delay in reaching Kik server',
      70: u'push notification sent',
      78: u'delivered after offline',
      94: u'read after offline'
  }

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.CopyToDict()

    message_type = event_values.get(u'message_type', None)
    if message_type is not None:
      event_values[u'message_type'] = (
          self._MESSAGE_TYPE.get(message_type, u'UNKNOWN'))

    message_status = event_values.get(u'message_status', None)
    if message_status is not None:
      event_values[u'message_status'] = (
          self._MESSAGE_STATUS.get(message_status, u'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(KikIOSMessageFormatter)
