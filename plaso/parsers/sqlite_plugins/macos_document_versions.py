# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS document revision database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacOSDocumentVersionsEventData(events.EventData):
  """MacOS document revision event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): date and time the version
        information was created.
    last_seen_time (dfdatetime.DateTimeValues): date and time and the original
       file was last seen (replicated).
    name (str): name of the original file.
    path (str): path from the original file.
    query (str): SQL query that was used to obtain the event data.
    user_sid (str): user identifier that open the file.
    version_path (str): path to the version copy of the original file.
  """

  DATA_TYPE = 'macos:document_versions:file'

  def __init__(self):
    """Initializes event data."""
    super(MacOSDocumentVersionsEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.creation_time = None
    self.last_seen_time = None
    self.name = None
    self.path = None
    self.query = None
    self.user_sid = None
    self.version_path = None


class MacOSDocumentVersionsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS document revision database files."""

  NAME = 'mac_document_versions'
  DATA_FORMAT = 'MacOS document revisions SQLite database file'

  REQUIRED_STRUCTURE = {
      'files': frozenset([
          'file_name', 'file_path', 'file_last_seen', 'file_storage_id']),
      'generations': frozenset([
          'generation_path', 'generation_add_time', 'generation_storage_id'])}

  # Define the needed queries.
  # name: name from the original file.
  # path: path from the original file (include the file)
  # last_time: last time when the file was replicated.
  # version_path: path where the version is stored.
  # version_time: the timestamp when the version was created.
  QUERIES = [
      (('SELECT f.file_name AS name, f.file_path AS path, '
        'f.file_last_seen AS last_time, g.generation_path AS version_path, '
        'g.generation_add_time AS version_time FROM files f, generations g '
        'WHERE f.file_storage_id = g.generation_storage_id;'),
       'DocumentVersionsRow')]

  SCHEMAS = [{
      'files': (
          'CREATE TABLE files (file_row_id INTEGER PRIMARY KEY ASC, file_name '
          'TEXT, file_parent_id INTEGER, file_path TEXT, file_inode INTEGER, '
          'file_last_seen INTEGER NOT NULL DEFAULT 0, file_status INTEGER NOT '
          'NULL DEFAULT 1, file_storage_id INTEGER NOT NULL)'),
      'generations': (
          'CREATE TABLE generations (generation_id INTEGER PRIMARY KEY ASC, '
          'generation_storage_id INTEGER NOT NULL, generation_name TEXT NOT '
          'NULL, generation_client_id TEXT NOT NULL, generation_path TEXT '
          'UNIQUE, generation_options INTEGER NOT NULL DEFAULT 1, '
          'generation_status INTEGER NOT NULL DEFAULT 1, generation_add_time '
          'INTEGER NOT NULL DEFAULT 0, generation_size INTEGER NOT NULL '
          'DEFAULT 0, generation_prunable INTEGER NOT NULL DEFAULT 0)'),
      'storage': (
          'CREATE TABLE storage (storage_id INTEGER PRIMARY KEY ASC '
          'AUTOINCREMENT, storage_options INTEGER NOT NULL DEFAULT 1, '
          'storage_status INTEGER NOT NULL DEFAULT 1)')}]

  # The SQL field path is the relative path from DocumentRevisions.
  # For this reason the Path to the program has to be added at the beginning.
  ROOT_VERSION_PATH = '/.DocumentRevisions-V100/'

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

  def DocumentVersionsRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a document versions row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    # version_path = "PerUser/UserID/xx/client_id/version_file"
    # where PerUser and UserID are a real directories.
    version_path = self._GetRowValue(query_hash, row, 'version_path')
    path = self._GetRowValue(query_hash, row, 'path')

    paths = version_path.split('/')
    if len(paths) < 2 or not paths[1].isdigit():
      user_sid = ''
    else:
      user_sid = paths[1]
    version_path = self.ROOT_VERSION_PATH + version_path
    path, _, _ = path.rpartition('/')

    event_data = MacOSDocumentVersionsEventData()
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'version_time')
    event_data.last_seen_time = self._GetDateTimeRowValue(
        query_hash, row, 'last_time')
    event_data.name = self._GetRowValue(query_hash, row, 'name')
    event_data.path = path
    event_data.query = query
    # Note that the user_sid value is expected to be a string.
    event_data.user_sid = '{0!s}'.format(user_sid)
    event_data.version_path = version_path

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(MacOSDocumentVersionsPlugin)
