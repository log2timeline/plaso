# -*- coding: utf-8 -*-
"""This file contains a parser for the Android contacts2 Call History.

Android Call History is stored in SQLite database files named contacts2.db.
"""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import py2to3
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidCallEventData(events.EventData):
  """Android Call event data.

  Attributes:
    call_type (str): type of call, such as: Incoming, Outgoing, or Missed.
    duration (int): number of seconds the call lasted.
    name (str): name associated to the remote party.
    number (str): phone number associated to the remote party.
  """

  DATA_TYPE = u'android:event:call'

  def __init__(self):
    """Initializes event data."""
    super(AndroidCallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.call_type = None
    self.duration = None
    self.name = None
    self.number = None


class AndroidCallPlugin(interface.SQLitePlugin):
  """Parse Android contacts2 database."""

  NAME = u'android_calls'
  DESCRIPTION = u'Parser for Android calls SQLite database files.'

  REQUIRED_TABLES = frozenset([u'calls'])

  # Define the needed queries.
  QUERIES = [
      (u'SELECT _id AS id, date, number, name, duration, type FROM calls',
       u'ParseCallsRow')]

  CALL_TYPE = {
      1: u'INCOMING',
      2: u'OUTGOING',
      3: u'MISSED'}

  def ParseCallsRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a Call record row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    call_type = self.CALL_TYPE.get(row['type'], u'UNKNOWN')
    duration = row['duration']
    timestamp = row['date']

    event_data = AndroidCallEventData()
    event_data.call_type = call_type
    event_data.duration = row['duration']
    event_data.name = row['name']
    event_data.number = row['number']
    event_data.offset = row['id']
    event_data.query = query

    date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(date_time, u'Call Started')
    parser_mediator.ProduceEventWithEventData(event, event_data)

    if duration:
      if isinstance(duration, py2to3.STRING_TYPES):
        try:
          duration = int(duration, 10)
        except ValueError:
          duration = 0

      # The duration is in seconds and the date value in milliseconds.
      timestamp += duration * 1000

      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'Call Ended')
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidCallPlugin)
