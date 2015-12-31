# -*- coding: utf-8 -*-
"""This file contains a parser for the Android SMS database.

Android SMS messages are stored in SQLite database files named mmssms.dbs.
"""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidSmsEvent(time_events.JavaTimeEvent):
  """Convenience class for an Android SMS event."""

  DATA_TYPE = u'android:messaging:sms'

  def __init__(self, java_time, identifier, address, sms_read, sms_type, body):
    """Initializes the event object.

    Args:
      java_time: The Java time value.
      identifier: The row identifier.
      address: The phone number associated to the sender/receiver.
      status:  Read or Unread.
      type: Sent or Received.
      body: Content of the SMS text message.
    """
    super(AndroidSmsEvent, self).__init__(
        java_time, eventdata.EventTimestamp.CREATION_TIME)
    self.offset = identifier
    self.address = address
    self.sms_read = sms_read
    self.sms_type = sms_type
    self.body = body


class AndroidSmsPlugin(interface.SQLitePlugin):
  """Parse Android SMS database."""

  NAME = u'android_sms'
  DESCRIPTION = u'Parser for Android text messages SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (u'SELECT _id AS id, address, date, read, type, body FROM sms',
       u'ParseSmsRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([u'sms'])

  SMS_TYPE = {
      1: u'RECEIVED',
      2: u'SENT'}
  SMS_READ = {
      0: u'UNREAD',
      1: u'READ'}

  def ParseSmsRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses an SMS row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    sms_type = self.SMS_TYPE.get(row['type'], u'UNKNOWN')
    sms_read = self.SMS_READ.get(row['read'], u'UNKNOWN')

    event_object = AndroidSmsEvent(
        row['date'], row['id'], row['address'], sms_read, sms_type,
        row['body'])
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(AndroidSmsPlugin)
