# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google Chrome extension activity database files."""

from dfdatetime import webkit_time as dfdatetime_webkit_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ChromeExtensionActivityEventData(events.EventData):
  """Chrome Extension Activity event data.

  Attributes:
    action_type (str): action type.
    activity_id (str): activity identifier.
    api_name (str): name of API.
    arg_url (str): URL argument.
    args (str): arguments.
    extension_id (str): extension identifier.
    other (str): other.
    page_title (str): title of webpage.
    page_url (str): URL of webpage.
    query (str): SQL query that was used to obtain the event data.
    recorded_time (dfdatetime.DateTimeValues): date and time the entry
        was recorded.
  """

  DATA_TYPE = 'chrome:extension_activity:activity_log'

  def __init__(self):
    """Initializes event data."""
    super(ChromeExtensionActivityEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.action_type = None
    self.activity_id = None
    self.api_name = None
    self.arg_url = None
    self.args = None
    self.extension_id = None
    self.other = None
    self.page_title = None
    self.page_url = None
    self.query = None
    self.recorded_time = None


class ChromeExtensionActivityPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Google Chrome extension activity database files.

  The Google Chrome extension activity database file is typically stored in:
  Extension Activity
  """

  NAME = 'chrome_extension_activity'
  DATA_FORMAT = 'Google Chrome extension activity SQLite database file'

  REQUIRED_STRUCTURE = {
      'activitylog_compressed': frozenset([
          'time', 'extension_id_x', 'action_type', 'api_name_x', 'args_x',
          'page_url_x', 'page_title_x', 'arg_url_x', 'other_x'])}

  QUERIES = [
      (('SELECT time, extension_id, action_type, api_name, args, page_url, '
        'page_title, arg_url, other, activity_id '
        'FROM activitylog_uncompressed ORDER BY time'),
       'ParseActivityLogUncompressedRow')]

  SCHEMAS = [{
      'activitylog_compressed': (
          'CREATE TABLE activitylog_compressed (count INTEGER NOT NULL '
          'DEFAULT 1, extension_id_x INTEGER NOT NULL, time INTEGER, '
          'action_type INTEGER, api_name_x INTEGER, args_x INTEGER, '
          'page_url_x INTEGER, page_title_x INTEGER, arg_url_x INTEGER, '
          'other_x INTEGER)'),
      'string_ids': (
          'CREATE TABLE string_ids (id INTEGER PRIMARY KEY, value TEXT NOT '
          'NULL)'),
      'url_ids': (
          'CREATE TABLE url_ids (id INTEGER PRIMARY KEY, value TEXT NOT '
          'NULL)')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.WebKitTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)

  def ParseActivityLogUncompressedRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses an activity log row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = ChromeExtensionActivityEventData()
    event_data.action_type = self._GetRowValue(query_hash, row, 'action_type')
    event_data.activity_id = self._GetRowValue(query_hash, row, 'activity_id')
    event_data.api_name = self._GetRowValue(query_hash, row, 'api_name')
    event_data.arg_url = self._GetRowValue(query_hash, row, 'arg_url')
    event_data.args = self._GetRowValue(query_hash, row, 'args')
    event_data.extension_id = self._GetRowValue(query_hash, row, 'extension_id')
    event_data.other = self._GetRowValue(query_hash, row, 'other')
    event_data.page_title = self._GetRowValue(query_hash, row, 'page_title')
    event_data.page_url = self._GetRowValue(query_hash, row, 'page_url')
    event_data.query = query
    event_data.recorded_time = self._GetDateTimeRowValue(
        query_hash, row, 'time')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(ChromeExtensionActivityPlugin)
