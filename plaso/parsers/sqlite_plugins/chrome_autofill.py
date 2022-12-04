# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google Chrome autofill database (Web Data) files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ChromeAutofillEventData(events.EventData):
  """Chrome Autofill event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): creation date and time of
        the autofill entry.
    field_name (str): name of form field.
    last_used_time (dfdatetime.DateTimeValues): last date and time
        the autofill entry was last used.
    query (str): SQL query that was used to obtain the event data.
    usage_count (int): count of times value has been used in field_name.
    value (str): value populated in form field.
  """

  DATA_TYPE = 'chrome:autofill:entry'

  def __init__(self):
    """Initializes event data."""
    super(ChromeAutofillEventData, self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.field_name = None
    self.last_used_time = None
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

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def ParseAutofillRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses an autofill entry row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = ChromeAutofillEventData()
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'date_created')
    event_data.field_name = self._GetRowValue(query_hash, row, 'name')
    event_data.last_used_time = self._GetDateTimeRowValue(
        query_hash, row, 'date_last_used')
    event_data.value = self._GetRowValue(query_hash, row, 'value')
    event_data.usage_count = self._GetRowValue(query_hash, row, 'count')
    event_data.query = query

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(ChromeAutofillPlugin)
