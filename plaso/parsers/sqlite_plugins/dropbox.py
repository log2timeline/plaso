# -*- coding: utf-8 -*-
"""SQLite parser plugin for Dropbox sync_history database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class DropboxSyncHistoryEventData(events.EventData):
  """Dropbox Sync History Database event data.

  Attributes:
    event_type (str): the event type
    file_event_type (str): the file event type
    direction (str): the source of the synchronisation event
    file_id (str): the ID of the file.
    local_path (str): the local path of the file.
  """

  DATA_TYPE = 'dropbox:sync_history:entry'

  def __init__(self):
    """Initializes event data."""
    super(DropboxSyncHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.event_type = None
    self.file_event_type = None
    self.direction = None
    self.file_id = None
    self.local_path = None


class DropboxSyncDatabasePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Dropbox sync_history.db database files.

  The Linux sync_history.db database is typically stored in:
  $HOME/.dropbox/instance1/sync_history.db

  The Windows 10 sync_history.db database is typically stored in:
  $HOME/AppData/Local/Dropbox/instance1/sync_history.db
  """

  NAME = 'dropbox'
  DATA_FORMAT = 'Dropbox sync history database (sync_history.db) file'

  REQUIRED_STRUCTURE = {
    'sync_history': frozenset(['timestamp', 'event_type', 'file_event_type',
        'direction', 'file_id', 'local_path'])}

  QUERIES = [
      ('SELECT timestamp, event_type, file_event_type, direction, file_id, '
       'local_path FROM sync_history;',
       'ParseSyncHistoryRow')]

  SCHEMAS = [{
      'sync_history': (
          'CREATE TABLE sync_history (event_type TEXT NOT NULL, file_event_type'
          ' TEXT, direction TEXT, file_id TEXT, local_path TEXT, timestamp '
          'INTEGER NOT NULL, other_user INTEGER')}]

  def ParseSyncHistoryRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a sync_history row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = DropboxSyncHistoryEventData()
    event_data.event_type = self._GetRowValue(query_hash, row, 'event_type')
    event_data.file_event_type = self._GetRowValue(
        query_hash, row, 'file_event_type')
    event_data.direction = self._GetRowValue(query_hash, row, 'direction')
    event_data.file_id = self._GetRowValue(query_hash, row, 'file_id')
    event_data.local_path = self._GetRowValue(query_hash, row, 'local_path')

    timestamp = self._GetRowValue(query_hash, row, 'timestamp')
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(DropboxSyncDatabasePlugin)