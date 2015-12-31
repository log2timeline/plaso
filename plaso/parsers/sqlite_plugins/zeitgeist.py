# -*- coding: utf-8 -*-
"""Plugin for the Zeitgeist SQLite database.

   Zeitgeist is a service which logs the user activities and events, anywhere
   from files opened to websites visited and conversations.
"""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ZeitgeistEvent(time_events.JavaTimeEvent):
  """Convenience class for a Zeitgeist event."""

  DATA_TYPE = u'zeitgeist:activity'

  def __init__(self, java_time, row_id, subject_uri):
    """Initializes the event object.

    Args:
      java_time: The Java time value.
      row_id: The identifier of the corresponding row.
      subject_uri: The Zeitgeist event.
    """
    super(ZeitgeistEvent, self).__init__(
        java_time, eventdata.EventTimestamp.UNKNOWN)

    self.offset = row_id
    self.subject_uri = subject_uri


class ZeitgeistPlugin(interface.SQLitePlugin):
  """SQLite plugin for Zeitgeist activity database."""

  NAME = u'zeitgeist'
  DESCRIPTION = u'Parser for Zeitgeist activity SQLite database files.'

  # TODO: Explore the database more and make this parser cover new findings.

  QUERIES = [
      (u'SELECT id, timestamp, subj_uri FROM event_view',
       u'ParseZeitgeistEventRow')]

  REQUIRED_TABLES = frozenset([u'event', u'actor'])

  def ParseZeitgeistEventRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses zeitgeist event row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_object = ZeitgeistEvent(
        row['timestamp'], row['id'], row['subj_uri'])
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(ZeitgeistPlugin)
