# -*- coding: utf-8 -*-
"""SQLite database plugin related functions and classes for testing."""

import os

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import sqlite

from tests.parsers import test_lib


class SQLitePluginTestCase(test_lib.ParserTestCase):
  """SQLite database plugin test case."""

  def _OpenDatabaseFile(self, path_segments, wal_path_segments=None):
    """Opens a SQLite database file.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      wal_path_segments (list[str]): path segments inside the test data
          directory of the SQLite WAL file.

    Returns:
      tuple: containing:
          file_entry (dfvfs.FileEntry): file entry of the SQLite database file.
          SQLiteDatabase: SQLite database file.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    file_entry = self._GetTestFileEntry(path_segments)

    wal_file_entry = None
    if wal_path_segments:
      wal_file_entry = self._GetTestFileEntry(wal_path_segments)

    database = sqlite.SQLiteDatabase(file_entry.name)
    file_object = file_entry.GetFileObject()

    if not wal_file_entry:
      database.Open(file_object)
    else:
      wal_file_object = wal_file_entry.GetFileObject()

      # Seek file_object to 0 so we can re-open the database with WAL file.
      file_object.seek(0, os.SEEK_SET)
      database.Open(file_object, wal_file_object=wal_file_object)

    return file_entry, database

  def _ParseDatabaseFileWithPlugin(
      self, path_segments, plugin, wal_path_segments=None):
    """Parses a file as a SQLite database with a specific plugin.

    This method will first test if a SQLite database contains the required
    tables and columns using plugin.CheckRequiredTablesAndColumns() and then
    extracts events using plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (SQLitePlugin): SQLite database plugin.
      wal_path_segments (list[str]): path segments inside the test data
          directory of the SQLite WAL file.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    parser_mediator = parsers_mediator.ParserMediator()

    storage_writer = self._CreateStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    file_entry, database = self._OpenDatabaseFile(
        path_segments, wal_path_segments=wal_path_segments)
    parser_mediator.SetFileEntry(file_entry)

    if file_entry:
      event_data_stream = events.EventDataStream()
      event_data_stream.path_spec = file_entry.path_spec

      parser_mediator.ProduceEventDataStream(event_data_stream)

    # AppendToParserChain needs to be run after SetFileEntry.
    parser_mediator.AppendToParserChain('sqlite')

    required_tables_and_column_exist = plugin.CheckRequiredTablesAndColumns(
        database)
    self.assertTrue(required_tables_and_column_exist)

    try:
      cache = sqlite.SQLiteCache()

      plugin.UpdateChainAndProcess(
          parser_mediator, cache=cache, database=database)
    finally:
      database.Close()

    return storage_writer
