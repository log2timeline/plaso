# -*- coding: utf-8 -*-
"""This file contains a parser for the Android contacts2 Call History.

Android Call History is stored in SQLite database files named contacts2.db.
"""

from plaso.events import time_events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidCallEvent(time_events.JavaTimeEvent):
  """Convenience class for an Android Call History event."""

  DATA_TYPE = 'android:event:call'

  def __init__(
      self, java_time, usage, identifier, number, name, duration, call_type):
    """Initializes the event object.

    Args:
      java_time: The Java time value.
      usage: The description of the usage of the time value.
      identifier: The row identifier.
      number: The phone number associated to the remote party.
      duration: The number of seconds the call lasted.
      call_type: Incoming, Outgoing, or Missed.
    """
    super(AndroidCallEvent, self).__init__(java_time, usage)
    self.offset = identifier
    self.number = number
    self.name = name
    self.duration = duration
    self.call_type = call_type


class AndroidCallPlugin(interface.SQLitePlugin):
  """Parse Android contacts2 database."""

  NAME = 'android_calls'
  DESCRIPTION = u'Parser for Android calls SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ('SELECT _id AS id, date, number, name, duration, type FROM calls',
       'ParseCallsRow')]

  CALL_TYPE = {
      1: u'INCOMING',
      2: u'OUTGOING',
      3: u'MISSED'}

  def ParseCallsRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a Call record row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    # Extract and lookup the call type.
    call_type = self.CALL_TYPE.get(row['type'], u'UNKNOWN')

    event_object = AndroidCallEvent(
        row['date'], u'Call Started', row['id'], row['number'], row['name'],
        row['duration'], call_type)
    parser_mediator.ProduceEvent(event_object, query=query)

    duration = row['duration']
    if isinstance(duration, basestring):
      try:
        duration = int(duration, 10)
      except ValueError:
        duration = 0

    if duration:
      # The duration is in seconds and the date value in milli seconds.
      duration *= 1000
      event_object = AndroidCallEvent(
          row['date'] + duration, u'Call Ended', row['id'], row['number'],
          row['name'], row['duration'], call_type)
      parser_mediator.ProduceEvent(event_object, query=query)



sqlite.SQLiteParser.RegisterPlugin(AndroidCallPlugin)
