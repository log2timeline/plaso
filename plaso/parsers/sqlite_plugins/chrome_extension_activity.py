# -*- coding: utf-8 -*-
"""Parser for the Google Chrome extension activity database files.

The Chrome extension activity is stored in SQLite database files named
Extension Activity.
"""

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

  DATA_TYPE = u'chrome:extension_activity:activity_log'

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

  NAME = u'chrome_extension_activity'
  DESCRIPTION = u'Parser for Chrome extension activity SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT time, extension_id, action_type, api_name, args, page_url, '
        u'page_title, arg_url, other, activity_id '
        u'FROM activitylog_uncompressed ORDER BY time'),
       u'ParseActivityLogUncompressedRow')]

  REQUIRED_TABLES = frozenset([
      u'activitylog_compressed', u'string_ids', u'url_ids'])

  SCHEMAS = [{
      u'activitylog_compressed': (
          u'CREATE TABLE activitylog_compressed (count INTEGER NOT NULL '
          u'DEFAULT 1, extension_id_x INTEGER NOT NULL, time INTEGER, '
          u'action_type INTEGER, api_name_x INTEGER, args_x INTEGER, '
          u'page_url_x INTEGER, page_title_x INTEGER, arg_url_x INTEGER, '
          u'other_x INTEGER)'),
      u'string_ids': (
          u'CREATE TABLE string_ids (id INTEGER PRIMARY KEY, value TEXT NOT '
          u'NULL)'),
      u'url_ids': (
          u'CREATE TABLE url_ids (id INTEGER PRIMARY KEY, value TEXT NOT '
          u'NULL)')}]

  def ParseActivityLogUncompressedRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses an activity log row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = ChromeExtensionActivityEventData()
    event_data.action_type = row['action_type']
    event_data.activity_id = row['activity_id']
    event_data.api_name = row['api_name']
    event_data.arg_url = row['arg_url']
    event_data.args = row['args']
    event_data.extension_id = row['extension_id']
    event_data.other = row['other']
    event_data.page_title = row['page_title']
    event_data.page_url = row['page_url']
    event_data.query = query

    timestamp = row['time']
    date_time = dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_UNKNOWN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ChromeExtensionActivityPlugin)
