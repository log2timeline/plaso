# -*- coding: utf-8 -*-
"""This file contains a parser for the iMessage database on OSX and iOS.

iMessage and SMS data in OSX and iOS are stored in SQLite databases named
chat.db and sms.db respectively.
"""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IMessageEventData(events.EventData):
  """iMessage and SMS event data.

  Attributes:
    attachment_location (str): location of the attachment.
    imessage_id (str): mobile number or email address the message was sent
        to or received from.
    message_type (int): value to indicate the message was sent (1) or
        received (0).
    read_receipt (bool): True if the message read receipt was received.
    service (str): service, which is either SMS or iMessage.
    text (str): content of the message.
  """

  DATA_TYPE = u'imessage:event:chat'

  def __init__(self):
    """Initializes event data."""
    super(IMessageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.attachment_location = None
    self.imessage_id = None
    self.message_type = None
    self.read_receipt = None
    self.service = None
    self.text = None


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
  REQUIRED_TABLES = frozenset([
      u'message', u'handle', u'attachment', u'message_attachment_join'])

  def ParseMessageRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = IMessageEventData()
    event_data.attachment_location = row['attachment_location']
    event_data.imessage_id = row['imessage_id']
    event_data.message_type = row['message_type']
    event_data.offset = row['ROWID']
    event_data.query = query
    event_data.read_receipt = row['read_receipt']
    event_data.service = row['service']
    event_data.text = row['text']

    timestamp = row['date']
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, eventdata.EventTimestamp.CREATION_TIME)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(IMessagePlugin)
