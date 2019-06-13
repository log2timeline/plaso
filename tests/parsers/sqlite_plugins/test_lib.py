# -*- coding: utf-8 -*-
"""SQLite database plugin related functions and classes for testing."""

from __future__ import unicode_literals

import os

from plaso.containers import sessions
from plaso.parsers import sqlite
from plaso.storage.fake import writer as fake_writer

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
    try:
      if not wal_file_entry:
        database.Open(file_object)
      else:
        wal_file_object = wal_file_entry.GetFileObject()

        # Seek file_object to 0 so we can re-open the database with WAL file.
        file_object.seek(0, os.SEEK_SET)
        try:
          database.Open(file_object, wal_file_object=wal_file_object)
        finally:
          wal_file_object.close()

    finally:
      file_object.close()

    return file_entry, database

  def _ParseDatabaseFileWithPlugin(
      self, path_segments, plugin, knowledge_base_values=None,
      wal_path_segments=None):
    """Parses a file as a SQLite database with a specific plugin.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (SQLitePlugin): SQLite database plugin.
      knowledge_base_values (Optional[dict[str, object]]): knowledge base
          values.
      wal_path_segments (list[str]): path segments inside the test data
          directory of the SQLite WAL file.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    file_entry, database = self._OpenDatabaseFile(
        path_segments, wal_path_segments=wal_path_segments)

    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=file_entry,
        knowledge_base_values=knowledge_base_values)

    parser_mediator.SetFileEntry(file_entry)

    # AppendToParserChain needs to be run after SetFileEntry.
    parser_mediator.AppendToParserChain(plugin)

    try:
      cache = sqlite.SQLiteCache()

      plugin.Process(parser_mediator, cache=cache, database=database)
    finally:
      database.Close()

    return storage_writer
