# -*- coding: utf-8 -*-
"""Plugin for the Zeitgeist SQLite database.

Zeitgeist is a service which logs the user activities and events, anywhere
from files opened to websites visited and conversations.
"""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ZeitgeistActivityEventData(events.EventData):
  """Zeitgeist activity event data.

  Attributes:
    subject_uri (str): subject URI.
  """

  DATA_TYPE = u'zeitgeist:activity'

  def __init__(self):
    """Initializes event data."""
    super(ZeitgeistActivityEventData, self).__init__(data_type=self.DATA_TYPE)
    self.subject_uri = None


class ZeitgeistActivityDatabasePlugin(interface.SQLitePlugin):
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
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = ZeitgeistActivityEventData()
    event_data.offset = row['id']
    event_data.query = query
    event_data.subject_uri = row['subj_uri']

    date_time = dfdatetime_java_time.JavaTime(timestamp=row['timestamp'])
    event = time_events.DateTimeValuesEvent(
        date_time, eventdata.EventTimestamp.UNKNOWN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ZeitgeistActivityDatabasePlugin)
