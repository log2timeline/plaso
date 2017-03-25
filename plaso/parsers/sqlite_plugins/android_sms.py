# -*- coding: utf-8 -*-
"""This file contains a parser for the Android SMS database.

Android SMS messages are stored in SQLite database files named mmssms.dbs.
"""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidSMSEventData(events.EventData):
  """Android SMS event data.

  Attributes:
    address (str): phone number associated to the sender or receiver.
    body (str): content of the SMS text message.
    sms_read (str): message read status, either Read or Unread.
    sms_type (str): message type, either Sent or Received.
  """

  DATA_TYPE = u'android:messaging:sms'

  def __init__(self):
    """Initializes event data."""
    super(AndroidSMSEventData, self).__init__(data_type=self.DATA_TYPE)
    self.address = None
    self.body = None
    self.sms_read = None
    self.sms_type = None


class AndroidSMSPlugin(interface.SQLitePlugin):
  """Parser for Android SMS databases."""

  NAME = u'android_sms'
  DESCRIPTION = u'Parser for Android text messages SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (u'SELECT _id AS id, address, date, read, type, body FROM sms',
       u'ParseSmsRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([u'sms'])

  # TODO: Move this functionality to the formatter.
  SMS_TYPE = {
      1: u'RECEIVED',
      2: u'SENT'}
  SMS_READ = {
      0: u'UNREAD',
      1: u'READ'}

  def ParseSmsRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses an SMS row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = AndroidSMSEventData()
    event_data.address = row['address']
    event_data.body = row['body']
    event_data.offset = row['id']
    event_data.query = query
    event_data.sms_read = self.SMS_READ.get(row['read'], u'UNKNOWN')
    event_data.sms_type = self.SMS_TYPE.get(row['type'], u'UNKNOWN')

    date_time = dfdatetime_java_time.JavaTime(timestamp=row['date'])
    event = time_events.DateTimeValuesEvent(
        date_time, eventdata.EventTimestamp.CREATION_TIME)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidSMSPlugin)
