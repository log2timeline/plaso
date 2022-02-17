# -*- coding: utf-8 -*-
"""SQLite parser plugin for Dropbox sync_history database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import sqlite


class DropboxSyncHistoryEventData(events.EventData):
  """Dropbox Sync History Database event data.

  Attributes:
    event_type (str): the event type
    file_event_type (str): the file event type
    direction (str): the source of the synchronisation event
    file_id (str): the ID of the file.
    local_path (str): the local path of the file.
  """
  pass

  DATA_TYPE = 'dropbox:sync:entry'

  def __init__(self):
    """Initializes event data."""
    super(DropboxSyncHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.event_type = None
    self.file_event_type = None
    self.direction = None
    self.file_id = None
    self.local_path = None


class DropboxSyncDatabasePlugin(interface.SqlitePlugin):
  """SQLite parser plugin for Dropbox sync_history.db database files.

  The Linux sync_history.db database is typically stored in:
  $HOME/AppData/Local/Dropbox/instance1/sync_history.db

  The Windows 10 sync_history.db database is typically stored in:
  $HOME/AppData/Local/Dropbox/instance1/sync_history.db
  """

  NAME = 'dropbox'
  DATA_FORMAT = 'Dropbox Desktop client'

  REQUIRED_STRUCTURE = {
    'sync_history': frozenset(['timestamp', 'event_data', 'file_event_type',
        'direction', 'file_id', 'local_path'])}

  QUERIES = [(
      ('SELECT timestamp, event_type, file_event_type, direction, file_id, '
       'local_path, other_user'),
       'ParseSyncHistoryRow')]

  SCHEMAS = [{
      'sync_history_old': (
          'CREATE TABLE sync_history (event_type TEXT NOT NULL, file_event_type'
          ' TEXT, direction TEXT, file_id TEXT, local_path TEXT, timestamp'
          ' INTEGER NOT NULL'),
      'sync_history': (
          'CREATE TABLE sync_history (event_type TEXT NOT NULL, file_event_type'
          ' TEXT, direction TEXT, file_id TEXT, local_path TEXT, timestamp '
          'INTEGER NOT NULL, other_user INTEGER')}]

  def ParseSyncHistoryRow(
      self, parser_mediator, query, row, **unused_kwargs):
      """Parses a sync_event row.

      Args:
        parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
        query (str): query that created the row.
        row (sqlite3.Row): row.
      """
      query_hash = hash(query)

      event_data = DropboxSyncDatabasePlugin()
      event_data.event_type = self._GetRowValue(query_hash, row, 'event_type')
      event_data.file_event_type = self._GetRowValue(
          query_hash, row, 'file_event_type')
      event_data.direction = self._GetRowValue(query_hash, row, 'direction')
      event_data.file_id = self._GetRowValue(query_hash, row, 'file_id')
      event_data.local_path = self._GetRowValue(query_hash, row, 'local_path')

      timestamp = self._GetRowValue(query_hash, row, 'timestamp')
      if timestamp:
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(DropboxSyncDatabasePlugin)
