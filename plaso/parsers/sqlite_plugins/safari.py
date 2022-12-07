# -*- coding: utf-8 -*-
"""SQLite parser plugin for Safari history database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class SafariHistoryPageVisitedEventData(events.EventData):
  """Safari history event data.

  Attributes:
    host (str): hostname of the server.
    last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
        last visited.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    title (str): title of the webpage visited.
    url (str): URL visited.
    visit_count (int): number of times the website was visited.
    was_http_non_get (bool): True if the webpage was visited using a
        non-GET HTTP request.
  """

  DATA_TYPE = 'safari:history:visit_sqlite'

  def __init__(self):
    """Initializes event data."""
    super(SafariHistoryPageVisitedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.host = None
    self.last_visited_time = None
    self.offset = None
    self.query = None
    self.title = None
    self.url = None
    self.visit_count = None
    self.visit_redirect_source = None
    self.was_http_non_get = None


class SafariHistoryPluginSqlite(interface.SQLitePlugin):
  """SQLite parser plugin for Safari history database files.

  The Safari history database file is typically stored in:
  History.db
  """

  NAME = 'safari_historydb'
  DATA_FORMAT = 'Safari history SQLite database (History.db) file'

  REQUIRED_STRUCTURE = {
      'history_items': frozenset([
          'id', 'url', 'visit_count']),
      'history_visits': frozenset([
          'id', 'history_item', 'visit_time', 'redirect_destination', 'title',
          'http_non_get', 'redirect_source'])}

  QUERIES = [
      (('SELECT history_items.id, history_items.url, history_items.visit'
        '_count, history_visits.id AS visit_id, history_visits.history_item,'
        'history_visits.visit_time, history_visits.redirect_destination, '
        'history_visits.title, history_visits.http_non_get, '
        'history_visits.redirect_source '
        'FROM history_items, history_visits '
        'WHERE history_items.id = history_visits.history_item '
        'ORDER BY history_visits.visit_time'), 'ParsePageVisitRow')]

  SCHEMAS = [{
      'history_client_versions': (
          'CREATE TABLE history_client_versions (client_version INTEGER '
          'PRIMARY KEY,last_seen REAL NOT NULL)'),
      'history_event_listeners': (
          'CREATE TABLE history_event_listeners (listener_name TEXT PRIMARY '
          'KEY NOT NULL UNIQUE,last_seen REAL NOT NULL)'),
      'history_events': (
          'CREATE TABLE history_events (id INTEGER PRIMARY KEY '
          'AUTOINCREMENT,event_type TEXT NOT NULL,event_time REAL NOT '
          'NULL,pending_listeners TEXT NOT NULL,value BLOB)'),
      'history_items': (
          'CREATE TABLE history_items (id INTEGER PRIMARY KEY '
          'AUTOINCREMENT,url TEXT NOT NULL UNIQUE,domain_expansion TEXT '
          'NULL,visit_count INTEGER NOT NULL,daily_visit_counts BLOB NOT '
          'NULL,weekly_visit_counts BLOB NULL,autocomplete_triggers BLOB '
          'NULL,should_recompute_derived_visit_counts INTEGER NOT '
          'NULL,visit_count_score INTEGER NOT NULL)'),
      'history_tombstones': (
          'CREATE TABLE history_tombstones (id INTEGER PRIMARY KEY '
          'AUTOINCREMENT,start_time REAL NOT NULL,end_time REAL NOT NULL,url '
          'TEXT,generation INTEGER NOT NULL DEFAULT 0)'),
      'history_visits': (
          'CREATE TABLE history_visits (id INTEGER PRIMARY KEY '
          'AUTOINCREMENT,history_item INTEGER NOT NULL REFERENCES '
          'history_items(id) ON DELETE CASCADE,visit_time REAL NOT NULL,title '
          'TEXT NULL,load_successful BOOLEAN NOT NULL DEFAULT 1,http_non_get '
          'BOOLEAN NOT NULL DEFAULT 0,synthesized BOOLEAN NOT NULL DEFAULT '
          '0,redirect_source INTEGER NULL UNIQUE REFERENCES '
          'history_visits(id) ON DELETE CASCADE,redirect_destination INTEGER '
          'NULL UNIQUE REFERENCES history_visits(id) ON DELETE CASCADE,origin '
          'INTEGER NOT NULL DEFAULT 0,generation INTEGER NOT NULL DEFAULT '
          '0,attributes INTEGER NOT NULL DEFAULT 0,score INTEGER NOT NULL '
          'DEFAULT 0)'),
      'metadata': (
          'CREATE TABLE metadata (key TEXT NOT NULL UNIQUE, value)')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  def ParsePageVisitRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a visited row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    was_http_non_get = self._GetRowValue(query_hash, row, 'http_non_get')

    event_data = SafariHistoryPageVisitedEventData()
    event_data.last_visited_time = self._GetDateTimeRowValue(
        query_hash, row, 'visit_time')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.title = self._GetRowValue(query_hash, row, 'title') or None
    event_data.url = self._GetRowValue(query_hash, row, 'url')
    event_data.visit_count = self._GetRowValue(query_hash, row, 'visit_count')
    event_data.was_http_non_get = bool(was_http_non_get)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(SafariHistoryPluginSqlite)
