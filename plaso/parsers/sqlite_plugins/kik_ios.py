# -*- coding: utf-8 -*-
"""This file contains a parser for the Kik database on iOS.

Kik messages on iOS devices are stored in an
SQLite database file named kik.sqlite.
"""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class KikIOSMessageEvent(time_events.CocoaTimeEvent):
  """Convenience class for a Kik message event."""

  DATA_TYPE = u'ios:kik:messaging'

  def __init__(
      self, cocoa_time, identifier, username, displayname,
      message_status, message_type, body):
    """Initializes the event object.

    Args:
      cocoa_time: The Cocoa time value.
      identifier: The row identifier.
      username: The unique username of the sender/receiver.
      message_status:  Read, unread, not sent, delivered, etc.
      message_type: Sent or Received.
      body: Content of the message.
    """
    super(KikIOSMessageEvent, self).__init__(
        cocoa_time, eventdata.EventTimestamp.CREATION_TIME)
    self.offset = identifier
    self.username = username
    self.displayname = displayname
    self.message_status = message_status
    self.message_type = message_type
    self.body = body


class KikIOSPlugin(interface.SQLitePlugin):
  """SQLite plugin for Kik iOS database."""

  NAME = u'kik_messenger'
  DESCRIPTION = u'Parser for iOS Kik messenger SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (u'SELECT a.Z_PK AS id, b.ZUSERNAME, b.ZDISPLAYNAME,'
       u'a.ZRECEIVEDTIMESTAMP, a.ZSTATE, a.ZTYPE, a.ZBODY '
       u'FROM ZKIKMESSAGE a JOIN ZKIKUSER b ON b.ZEXTRA = a.ZUSER',
       u'ParseMessageRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([u'ZKIKMESSAGE', u'ZKIKUSER'])

  def ParseMessageRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_object = KikIOSMessageEvent(
        row['ZRECEIVEDTIMESTAMP'], row['id'], row['ZUSERNAME'],
        row['ZDISPLAYNAME'], row['ZSTATE'], row['ZTYPE'], row['ZBODY'])
    parser_mediator.ProduceEvent(event_object, query=query)

sqlite.SQLiteParser.RegisterPlugin(KikIOSPlugin)
