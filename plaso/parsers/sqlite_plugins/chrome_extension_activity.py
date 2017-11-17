# -*- coding: utf-8 -*-
"""Parser for the Google Chrome extension activity database files.

The Chrome extension activity is stored in SQLite database files named
Extension Activity.
"""

from __future__ import unicode_literals

from dfdatetime import webkit_time as dfdatetime_webkit_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
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


class ChromeExtensionActivityPlugin(interface.SQLitePlugin):
  """Plugin to parse Chrome extension activity database files."""

  NAME = 'chrome_extension_activity'
  DESCRIPTION = 'Parser for Chrome extension activity SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (('SELECT time, extension_id, action_type, api_name, args, page_url, '
        'page_title, arg_url, other, activity_id '
        'FROM activitylog_uncompressed ORDER BY time'),
       'ParseActivityLogUncompressedRow')]

  REQUIRED_TABLES = frozenset([
      'activitylog_compressed', 'string_ids', 'url_ids'])

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

  def ParseActivityLogUncompressedRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses an activity log row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
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

    timestamp = self._GetRowValue(query_hash, row, 'time')
    date_time = dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_UNKNOWN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ChromeExtensionActivityPlugin)
