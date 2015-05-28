# -*- coding: utf-8 -*-
"""Parser for the Google Chrome extension activity database files.

   The Chrome extension activity is stored in SQLite database files named
   Extension Activity.
"""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ChromeExtensionActivityEvent(time_events.WebKitTimeEvent):
  """Convenience class for a Chrome Extension Activity event."""
  DATA_TYPE = u'chrome:extension_activity:activity_log'

  def __init__(self, row):
    """Initializes the event object.

    Args:
      row: The row resulting from the query (instance of sqlite3.Row).
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    # TODO: change the timestamp usage from unknown to something else.
    super(ChromeExtensionActivityEvent, self).__init__(
        row['time'], eventdata.EventTimestamp.UNKNOWN)

    self.extension_id = row['extension_id']
    self.action_type = row['action_type']
    self.api_name = row['api_name']
    self.args = row['args']
    self.page_url = row['page_url']
    self.page_title = row['page_title']
    self.arg_url = row['arg_url']
    self.other = row['other']
    self.activity_id = row['activity_id']


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

  def ParseActivityLogUncompressedRow(
      self, parser_mediator, row, query=None,
      **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      row: The row resulting from the query (instance of sqlite3.Row).
      query: Optional query string. The default is None.
    """
    event_object = ChromeExtensionActivityEvent(row)
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(ChromeExtensionActivityPlugin)
