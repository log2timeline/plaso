# -*- coding: utf-8 -*-
"""Parser for the Safari History files.

The Safari History is stored in SQLite database files named History.db
"""
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class SafariHistoryPageVisitedEventData(events.EventData):
  """Safari history event data.
  Attributes:
    title (str): title of the webpage visited.
    url (str): URL visited.
    host(str): Host name of the host server
    visit_count (int): number of times the website was visited.
    was_http_non_get (bool): True if the webpage was
     visited using a non-GET HTTP request.
  """

  DATA_TYPE = u'safari:history:visit_sqlite'

  def __init__(self):
    """Initializes event data."""
    super(SafariHistoryPageVisitedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.title = None
    self.url = None
    self.visit_count = None
    self.host = None
    self.was_http_non_get = None
    self.visit_redirect_source = None


class SafariHistoryPluginSqlite(interface.SQLitePlugin):
  """Parse Safari History Files.
  Safari history file is stored in a SQLite database file name History.DB
  """
  NAME = u'safari_history'
  DESCRIPTION = u'Parser for Safari history SQLite database files.'

  #Define the needed queries.

  QUERIES = [
  			 ((u'SELECT history_items.id, history_items.url, history_items.visit'
          u'_count, history_visits.id AS visit_id, history_visits.history_item,'
          u'history_visits.visit_time, history_visits.redirect_destination, '
          u'history_visits.title, history_visits.http_non_get, '
          u'history_visits.redirect_source, history_items.domain_expansion '
  			  u'FROM history_items, history_visits '
          u'WHERE history_items.id = history_visits.history_item '
  			  u'ORDER BY history_visits.visit_time'), u'ParsePageVisitRow')]
  			
  # The required tables
  REQUIRED_TABLES = frozenset([u'history_items',u'history_visits'])

  SCHEMAS =[{
      u'history_items': (
  	    u'CREATE TABLE history_items (id INTEGER PRIMARY KEY AUTOINCREMENT, '
  	    u'url TEXT NOT NULL UNIQUE,domain_expansion TEXT NULL, '
  	    u'visit_count INTEGER NOT NULL, daily_visit_counts BLOB NOT NULL, '
  	    u'weekly_visit_counts BLOB NULL, autocomplete_triggers BLOB NULL, '
  	    u'should_recompute_derived_visit_counts INTEGER NOT NULL, '
        u'visit_count_score INTEGER NOT NULL)'),
		  u'history_tombstones': (
			  u'CREATE TABLE history_tombstones (id INTEGER PRIMARY KEY AUTOINCREMENT, '
			  u'start_time REAL NOT NULL, end_time REAL NOT NULL, '
			  u'url TEXT,generation INTEGER NOT NULL DEFAULT 0)'),
		  u'metadata': (
			  u'CREATE TABLE metadata (key TEXT NOT NULL UNIQUE, value)'),
		  u'history_client_versions': (
			  u'CREATE TABLE history_client_versions (client_version '
        u'INTEGER PRIMARY KEY, last_seen REAL NOT NULL)'),
		  u'history_event_listeners': (
			  u'CREATE TABLE history_event_listeners (listener_name '
        u'TEXT PRIMARY KEY, last_seen REAL NOT NULL)'),
		  u'history_events': (
			  u'CREATE TABLE history_events (id INTEGER PRIMARY KEY '
        u'AUTOINCREMENT, event_type TEXT NOT NULL, '
			  u'event_time REAL NOT NULL, pending_listeners TEXT NOT NULL, value BLOB)'),
		  u'history_visits': (
			  u'CREATE TABLE history_visits (id INTEGER PRIMARY KEY AUTOINCREMENT, '
			  u'history_item INTEGER NOT NULL REFERENCES history_items(id) ON DELETE CASCADE, '
        u'visit_time REAL NOT NULL, title TEXT NULL,load_successful '
        u'BOOLEAN NOT NULL DEFAULT 1, http_non_get BOOLEAN NOT NULL DEFAULT 0, '
			  u'synthesized BOOLEAN NOT NULL DEFAULT 0, redirect_source '
        u'INTEGER NULL UNIQUE REFERENCES history_visits(id) '
			  u'ON DELETE CASCADE, redirect_destination INTEGER NULL UNIQUE '
        u'REFERENCES history_visits(id) ON DELETE CASCADE, '
			  u'origin INTEGER NOT NULL DEFAULT 0, generation INTEGER NOT NULL DEFAULT 0, '
			  u'attributes INTEGER NOT NULL DEFAULT 0, score INTEGER NOT NULL DEFAULT 0)')}]

  def _GetHostname(self, url):
    """Retrieves the hostname from a full URL.
    Args:
      url (str): full URL.
    Returns:
      str: hostname or full URL if not hostname could be retrieved.
    """
    if url.startswith(u'http') or url.startswith(u'ftp'):
      _, _, uri = url.partition(u'//')
      hostname, _, _ = uri.partition(u'/')
      return hostname

    if url.startswith(u'about'):
      hostname, _, _ = url.partition(u'/')
      return hostname

    return url



  def ParsePageVisitRow(self, parser_mediator, row, cache=None, 
    database=None, query=None, **unused_kwargs):

    """Parses a visited row.
    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      cache (Optional[SQLiteCache]): cache.
      database (Optional[SQLiteDatabase]): database.
      query (Optional[str]): query.
    """
      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".

      # Todo: Extras 

    event_data=SafariHistoryPageVisitedEventData()
    event_data.offset = row['id']
    event_data.query = query
    event_data.title = row['title']
    event_data.url = row['url']
    event_data.visit_count = row['visit_count']
    event_data.host = self._GetHostname(row['url'])
    event_data.was_http_non_get = bool(row['http_non_get'])
   
     

    timestamp = row['visit_time']
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_LAST_VISITED)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(SafariHistoryPluginSqlite)
