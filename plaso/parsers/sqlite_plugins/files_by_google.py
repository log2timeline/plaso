# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google Files by Google database (Web Data) files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class FilesByGoogleEventData(events.EventData):
  """Files by Google event data.

  Attributes:
    date_modified (dfdatetime.DateTimeValues): last modified date and time of
        the each file.
    root_path (str): memory location.
    root_relative_path (str): root path of a file.
    file_name (str): name of a file.
    file_size (int): size of a file.
    mime_type (str): format of a file.
    media_type (str): file's media type.
    uri (str): character sequence that identifies a resource.
    is_hidden (int): mark of a hidden file.
    title (str): name of a file.
    parent_folder (str): file's parent folder.
    query (str): SQL query that was used to obtain the event data.
  """

  DATA_TYPE = 'android:files_by_google:record'

  def __init__(self):
    """Initializes event data."""
    super(FilesByGoogleEventData, self).__init__(data_type=self.DATA_TYPE)
    self.date_modified = None
    self.root_path = None
    self.root_relative_path = None
    self.file_name = None
    self.file_size = None
    self.mime_type = None
    self.media_type = None
    self.uri = None
    self.is_hidden = None
    self.title = None
    self.parent_folder = None
    self.query = None


class FilesByGooglePlugin(interface.SQLitePlugin):
  """
  SQLite parser plugin for Google "Files by Google" app database files.

  The Files by Google app database file is typically stored in:
  /data/user/0/com.google.android.apps.nbu.files/databases/files_master_database

  This SQLite database is used by the Files by Google app to manage and organize files on Android devices. 
  The database contains information on file metadata, including file names, paths, sizes, and types, 
  as well as records of storage locations.
  """

  NAME = 'files_by_google'
  DATA_FORMAT = 'Files by Google SQLite database (files_master_database) file'

  REQUIRED_STRUCTURE = {
      'autofill': frozenset([
          'file_date_modified_ms', 'root_path', 'root_relative_file_path', 'file_name', 'size', 'mime_type',
          'media_type', 'uri', 'is_hidden', 'title', 'parent_folder_name'])}

  QUERIES = [
      (('SELECT files_master_table.file_date_modified_ms, files_master_table.root_path, files_master_table.root_relative_file_path, '
        'files_master_table.file_name, files_master_table.size, files_master_table.mime_type, files_master_table.media_type, files_master_table.uri, '
        'files_master_table.is_hidden, files_master_table.title, files_master_table.parent_folder_name FROM files_master_table ORDER BY file_date_modified_ms '),
       'ParseFilesByGoogleRow')]

  SCHEMAS = [{
    'android_metadata':(
      'CREATE TABLE android_metadata (locale TEXT)'),
    'file_search_fts':(
       'CREATE VIRTUAL TABLE file_search_fts USING '
       'fts4(content="files_master_table", root_relative_file_path, '
       'title, artist, album)'),
    'file_search_fts_docsize':(
       'CREATE TABLE file_search_fts_docsize(docid INTEGER PRIMARY KEY, '
       'size BLOB)'),
    'file_search_fts_segdir':(
       'CREATE TABLE file_search_fts_segdir(level INTEGER, idx INTEGER, '
       'start_block INTEGER, leaves_end_block INTEGER, '
       'end_block INTEGER, root BLOB, '
       'PRIMARY KEY(level, idx))'),
    'file_search_fts_segments':(
       'CREATE TABLE file_search_fts_segments(blockid INTEGER PRIMARY KEY, '
       'block BLOB)'),
    'file_search_fts_stat':(
       'CREATE TABLE file_search_fts_stat(id INTEGER PRIMARY KEY, '
       'value BLOB)'),
    'files_master_table':(
       'CREATE TABLE files_master_table(id INTEGER PRIMARY KEY AUTOINCREMENT, '
       'media_store_id INTEGER, root_path TEXT NOT NULL DEFAULT '', '
       'root_relative_file_path TEXT NOT NULL DEFAULT '', file_name TEXT NOT NULL, '
       'size INTEGER NOT NULL, file_date_modified_ms INTEGER NOT NULL, '
       'storage_location INTEGER NOT NULL, mime_type TEXT, '
       'media_type INTEGER, uri TEXT NOT NULL, '
       'is_hidden INTEGER NOT NULL, title TEXT, '
       'artist TEXT, album TEXT, '
       'parent_folder_name TEXT COLLATE NOCASE, UNIQUE (media_store_id), '
       'UNIQUE (uri))'),
    'media_store_scan_state_table':(
       'CREATE TABLE media_store_scan_state_table(id INTEGER NOT NULL DEFAULT 0 UNIQUE, '
       'largest_scanned_date_modified_ms INTEGER NOT NULL, '
       'largest_scanned_media_store_id INTEGER NOT NULL)'),
    'post_file_scan_tasks_state_table':(
       'CREATE TABLE post_file_scan_tasks_state_table(task_type INTEGER NOT NULL UNIQUE, '
       'largest_processed_file_id INTEGER NOT NULL, '
       'last_processed_timestamp_ms INTEGER NOT NULL)'),
    'scan_log_table':(
       'CREATE TABLE scan_log_table(id INTEGER PRIMARY KEY AUTOINCREMENT, '
       'start_timestamp INTEGER NOT NULL DEFAULT 0, '
       'end_timestamp INTEGER NOT NULL DEFAULT 0, '
       'updated_items_count INTEGER NOT NULL DEFAULT 0, scan_type INTEGER NOT NULL, '
       'scan_result INTEGER NOT NULL DEFAULT 0)'),
    'file_consumption_data_table':(
       'CREATE TABLE file_consumption_data_table(id INTEGER PRIMARY KEY AUTOINCREMENT, '
       'main_file_table_id INTEGER NOT NULL, play_state INTEGER, '
       'duration INTEGER, play_position INTEGER, '
       'fully_played_count INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(main_file_table_id) '
       'REFERENCES files_master_table(id) ON DELETE CASCADE)'),
    'file_open_info_table':(
       'CREATE TABLE file_open_info_table(file_id INTEGER NOT NULL, '
       'file_open_time_stamp_ms INTEGER NOT NULL,  UNIQUE(file_id, '
       'file_open_time_stamp_ms), FOREIGN KEY(file_id) REFERENCES files_master_table(id) '
       'ON DELETE CASCADE)'),
    'files_classification_table':(
       'CREATE TABLE files_classification_table(file_id INTEGER NOT NULL, '
       'classification INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(file_id) '
       'REFERENCES files_master_table(id) ON DELETE CASCADE)'),
    'files_metadata_table':(
       'CREATE TABLE files_metadata_table(file_id INTEGER UNIQUE NOT NULL, '
       'title TEXT, artist TEXT, '
       'album TEXT, is_drm_protected INTEGER NOT NULL DEFAULT 0, '
       'latitude REAL, longitude REAL, '
       'width_px INTEGER, height_px INTEGER, '
       'duration_px INTEGER, track_number INTEGER, '
       'file_hash TEXT, taken_date_ms INTEGER, '
       'device_description TEXT, aperture DOUBLE, '
       'focal_length DOUBLE, exposure_time DOUBLE, '
       'iso_speed INTEGER, FOREIGN KEY(file_id) REFERENCES files_master_table(id) '
       'ON DELETE CASCADE)'),
    'nima_score_table':(
       'CREATE TABLE nima_score_table(file_id INTEGER NOT NULL, '
       'vg_score FLOAT NOT NULL, ava_score FLOAT NOT NULL, '
       'UNIQUE (file_id), FOREIGN KEY(file_id) REFERENCES files_master_table(id) '
       'ON DELETE CASCADE)'),
    'session_scan_log_table':(
       'CREATE TABLE session_scan_log_table(scan_id INTEGER NOT NULL, '
       'item_id INTEGER NOT NULL, FOREIGN KEY(scan_id) REFERENCES scan_log_table(id), '
       'FOREIGN KEY(item_id) REFERENCES files_master_table(id))')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTimeInMilliseconds: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTimeInMilliseconds(timestamp=timestamp)

  def ParseFilesByGoogleRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses an files by google entry row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = FilesByGoogleEventData()
    event_data.date_modified = self._GetDateTimeRowValue(
        query_hash, row, 'file_date_modified_ms')
    event_data.root_path = self._GetRowValue(query_hash, row, 'root_path')
    event_data.root_relative_path = self._GetRowValue(
        query_hash, row, 'root_relative_file_path')
    event_data.file_name = self._GetRowValue(query_hash, row, 'file_name')
    event_data.file_size = self._GetRowValue(query_hash, row, 'size')
    event_data.mime_type = self._GetRowValue(query_hash, row, 'mime_type')
    event_data.media_type = self._GetRowValue(query_hash, row, 'media_type')
    event_data.uri = self._GetRowValue(query_hash, row, 'uri')
    event_data.is_hidden = self._GetRowValue(query_hash, row, 'is_hidden')
    event_data.title = self._GetRowValue(query_hash, row, 'title')
    event_data.parent_folder = self._GetRowValue(query_hash, row, 'parent_folder_name')
    event_data.query = query

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(FilesByGooglePlugin)
