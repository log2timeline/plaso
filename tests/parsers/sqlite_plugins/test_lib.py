# -*- coding: utf-8 -*-
"""SQLite database plugin related functions and classes for testing."""

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import sessions
from plaso.parsers import sqlite
from plaso.storage import fake_storage

from tests.parsers import test_lib


class SQLitePluginTestCase(test_lib.ParserTestCase):
  """The unit test case for SQLite database plugins."""

  def _ParseDatabaseFileWithPlugin(
      self, path_segments, plugin, cache=None,
      knowledge_base_values=None, wal_path=None):
    """Parses a file as a SQLite database with a specific plugin.

    Args:
      path_segments: a list of strings containinge the path segments inside
                     the test data directory.
      plugin: The plugin object that is used to extract an event
                     generator.
      cache: optional cache object (instance of SQLiteCache).
      knowledge_base_values: optional dict containing the knowledge base
                             values.
      wal_path: optional string containing the path to the SQLite WAL file.

    Returns:
      A storage writer object (instance of FakeStorageWriter).
    """
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=file_entry,
        knowledge_base_values=knowledge_base_values)

    parser_mediator.SetFileEntry(file_entry)

    wal_file_entry = None
    if wal_path:
      wal_path_spec = path_spec_factory.Factory.NewPathSpec(
          definitions.TYPE_INDICATOR_OS, location=wal_path)
      wal_file_entry = path_spec_resolver.Resolver.OpenFileEntry(wal_path_spec)

    # AppendToParserChain needs to be run after SetFileEntry.
    parser_mediator.AppendToParserChain(plugin)

    database = sqlite.SQLiteDatabase(file_entry.name)
    database_wal = None

    file_object = file_entry.GetFileObject()
    try:
      database.Open(file_object)
      if wal_file_entry:
        database_wal = sqlite.SQLiteDatabase(file_entry.name)
        wal_file_object = wal_file_entry.GetFileObject()
        # Seek file_object to 0 so we can re-open the database with WAL file.
        file_object.seek(0)
        try:
          database_wal.Open(file_object, wal_file_object=wal_file_object)
        finally:
          wal_file_object.close()
    finally:
      file_object.close()

    try:
      plugin.Process(
          parser_mediator, cache=cache, database=database,
          database_wal=database_wal, wal_file_entry=wal_file_entry)
    finally:
      database.Close()
      if database_wal:
        database_wal.Close()

    return storage_writer
