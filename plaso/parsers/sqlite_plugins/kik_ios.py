# -*- coding: utf-8 -*-
"""This file contains a parser for the Kik database on iOS.

Kik messages on iOS devices are stored in an
SQLite database file named kik.sqlite.
"""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class KikIOSMessageEventData(events.EventData):
  """Kik message event data.

  Args:
    body (str): content of the message.
    message_status (str): message status, such as:
        read, unread, not sent, delivered, etc.
    message_type (str): message type, either Sent or Received.
    username (str): unique username of the sender or receiver.
  """

  DATA_TYPE = u'ios:kik:messaging'

  def __init__(self):
    """Initializes event data."""
    super(KikIOSMessageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.displayname = None
    self.message_status = None
    self.message_type = None
    self.username = None


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
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = KikIOSMessageEventData()
    event_data.body = row['ZBODY']
    event_data.displayname = row['ZDISPLAYNAME']
    event_data.message_status = row['ZSTATE']
    event_data.message_type = row['ZTYPE']
    event_data.offset = row['id']
    event_data.query = query
    event_data.username = row['ZUSERNAME']

    # Convert the floating point value to an integer.
    timestamp = int(row['ZRECEIVEDTIMESTAMP'])
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, eventdata.EventTimestamp.CREATION_TIME)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(KikIOSPlugin)
