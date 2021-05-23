# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google Chrome autofill database (Web Data) files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ChromeAutofillEventData(events.EventData):
  """Chrome Autofill event data.

  Attributes:
    field_name (str): name of form field.
    query (str): SQL query that was used to obtain the event data.
    usage_count (int): count of times value has been used in field_name.
    value (str): value populated in form field.
  """

  DATA_TYPE = 'chrome:autofill:entry'

  def __init__(self):
    """Initializes event data."""
    super(ChromeAutofillEventData, self).__init__(data_type=self.DATA_TYPE)
    self.field_name = None
    self.query = None
    self.usage_count = None
    self.value = None


class ChromeAutofillPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Google Chrome autofill database (Web Data) files.

  The Google Chrome autofill database (Web Data) file is typically stored in:
  Web Data
  """

  NAME = 'chrome_autofill'
  DATA_FORMAT = 'Google Chrome autofill SQLite database (Web Data) file'

  REQUIRED_STRUCTURE = {
      'autofill': frozenset([
          'date_created', 'date_last_used', 'name', 'value', 'count'])}

  QUERIES = [
      (('SELECT autofill.date_created, autofill.date_last_used, autofill.name, '
        'autofill.value, autofill.count FROM autofill ORDER BY date_created'),
       'ParseAutofillRow')]

  SCHEMAS = [{
      'autofill': (
          'CREATE TABLE autofill (name VARCHAR, value VARCHAR, '
          'value_lower VARCHAR, date_created INTEGER DEFAULT 0, '
          'date_last_used INTEGER DEFAULT 0, count INTEGER DEFAULT 1, '
          'PRIMARY KEY (name, value));)')}]

  def ParseAutofillRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses an autofill entry row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = ChromeAutofillEventData()
    event_data.field_name = self._GetRowValue(query_hash, row, 'name')
    event_data.value = self._GetRowValue(query_hash, row, 'value')
    event_data.usage_count = self._GetRowValue(query_hash, row, 'count')
    event_data.query = query

    # Create one event for the first time an autofill entry was used
    timestamp = self._GetRowValue(query_hash, row, 'date_created')
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    # If the autofill value has been used more than once, create another
    # event for the most recent time it was used.
    if event_data.usage_count > 1:
      timestamp = self._GetRowValue(query_hash, row, 'date_last_used')
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_USED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ChromeAutofillPlugin)
