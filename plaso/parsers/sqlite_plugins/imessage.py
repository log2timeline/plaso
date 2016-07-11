# -*- coding: utf-8 -*-
"""This file contains a parser for the iMessage database on OSX and iOS.

iMessage and SMS data in OSX and iOS are stored in SQLite databases named
chat.db and sms.db respectively.
"""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IMessageEvent(time_events.CocoaTimeEvent):
  """Convenience class for an iMessage and SMS event."""

  DATA_TYPE = u'imessage:event:chat'

  def __init__(
      self, cocoa_time, identifier, imessage_id, read_receipt,
      message_type, service, attachment_location, text):
    """Initializes the event object.

    Args:
      cocoa_time: an integer containing the Apple Cocoa time value - the number
                  of seconds passed since January 1, 2001 00:00:00 GMT.
      identifier: an integer containing the row number.
      imessage_id: a string containing the mobile number or email address the
                   message was sent to or received from.
      read_receipt: a boolean indicating that a message read receipt was
                    received.
      message_type: an integer indicating message was sent (1) or received (0).
      service: a string indicating SMS or iMessage.
      attachment: a boolean indicating that the message contained an attachment.
      text: content of the message.
    """
    super(IMessageEvent, self).__init__(
        cocoa_time, eventdata.EventTimestamp.CREATION_TIME)
    self.offset = identifier
    self.imessage_id = imessage_id
    self.read_receipt = read_receipt
    self.message_type = message_type
    self.service = service
    self.attachment_location = attachment_location
    self.text = text


class IMessagePlugin(interface.SQLitePlugin):
  """SQLite plugin for the iMessage and SMS database."""

  NAME = u'imessage'
  DESCRIPTION = u'Parser for the iMessage and SMS SQLite databases on OSX and '\
                u'iOS.'

  # Define the needed queries.
  QUERIES = [
      (u'SELECT m.date, m.ROWID, h.id AS imessage_id, m.is_read AS '
       u'read_receipt, m.is_from_me AS message_type, m.service, a.filename AS'
       u'"attachment_location", m.text FROM message AS m JOIN handle AS h ON '
       u'h.ROWID = m.handle_id LEFT OUTER JOIN message_attachment_join AS maj '
       u'ON m.ROWID = maj.message_id LEFT OUTER JOIN attachment AS a ON '
       u'maj.attachment_id = a.ROWID', u'ParseMessageRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([u'message', u'handle', u'attachment',
                               u'message_attachment_join'])

  def ParseMessageRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".
    event_object = IMessageEvent(
        row['date'], row['ROWID'], row['imessage_id'], row['read_receipt'],
        row['message_type'], row['service'], row['attachment_location'],
        row['text'])
    parser_mediator.ProduceEvent(event_object, query=query)

sqlite.SQLiteParser.RegisterPlugin(IMessagePlugin)
