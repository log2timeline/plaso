# -*- coding: utf-8 -*-
"""Plugin for Tango events from IOS."""
import base64

from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


from plaso.containers import time_events

class TangoIOSMessageEvent(time_events.JavaTimeEvent):
  DATA_TYPE = u''

  def __init__(self, timestamp, identifer, content, message_type, direction):
    """Initializes a Tango IOS message creation event.

    Args:
      timestamp: the Java timestamp which is an integer containing the number
                 of milliseconds since January 1, 1970, 00:00:00 UTC.
      identifer: TODO
      content: a string containing the message content.
      message_type: a numeric type containing the type of the message.
      direction: a numeric type containing the direction of the message.
    """
    super(TangoIOSMessageEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.CREATION_TIME)
    self.content = content
    self.message_type = message_type
    self.identifier = identifer
    self.direction = direction


class TangoIOSMessageCreationEvent(TangoIOSMessageEvent):
  """Convenience class for a Tango IOS message sent event."""
  DATA_TYPE = u'tango:ios:message_created'



class TangoIOSMessageSentEvent(TangoIOSMessageEvent):
  """Convenience class for a Tango IOS message sent event."""
  DATA_TYPE = u'tango:ios:message_sent'


class TangoIOSPlugin(interface.SQLitePlugin):
  """Parser for Tango IOS."""
  NAME = u'tango_ios'

  DESCRIPTION = u'Parser for the Tango database on IOS'

  QUERIES = frozenset([
    (u'SELECT messages.msg_id, messages.payload, messages.type, '
     u'messages.create_time, messages.send_time, messages.direction, '
     u'likes.msg_id, messages.del_status FROM messages '
     u'left join likes on messages.msg_id = likes.msg_id',
     u'ParseMessage'),
  ])

  REQUIRED_TABLES = frozenset([u'messages', u'likes'])

  def ParseMessage(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a message record from the database.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string']
    # and will raise "IndexError: Index must be int or string". All indexes are
    # thus raw strings.
    message_content = base64.b64decode(row['payload'])

    event = TangoIOSMessageSentEvent(
        row['send_time'], row['msg_id'], message_content, row['type'],
        row['direction'])
    parser_mediator.ProduceEvent(event, query=query)

    event = TangoIOSMessageCreationEvent(
        row['create_time'],row['msg_id'], message_content, row['type'],
        row['direction'])
    parser_mediator.ProduceEvent(event, query=query)


sqlite.SQLiteParser.RegisterPlugin(TangoIOSPlugin)
