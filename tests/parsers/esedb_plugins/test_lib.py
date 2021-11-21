# -*- coding: utf-8 -*-
"""ESEDB plugin related functions and classes for testing."""

from plaso.parsers import esedb
from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class ESEDBPluginTestCase(test_lib.ParserTestCase):
  """ESE database-based plugin test case."""

  def _ParseESEDBFileWithPlugin(
      self, path_segments, plugin, knowledge_base_values=None):
    """Parses a file as an ESE database file and returns an event generator.

    This method will first test if an ESE database contains the required tables
    using plugin.CheckRequiredTables() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (ESEDBPlugin): ESE database plugin.
      knowledge_base_values (Optional[dict[str, object]]): knowledge base
          values.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=file_entry,
        knowledge_base_values=knowledge_base_values)

    file_object = file_entry.GetFileObject()

    database = esedb.ESEDatabase()
    database.Open(file_object)

    try:
      required_tables_exist = plugin.CheckRequiredTables(database)
      self.assertTrue(required_tables_exist)

      cache = esedb.ESEDBCache()
      plugin.Process(parser_mediator, cache=cache, database=database)

    finally:
      database.Close()

    return storage_writer
