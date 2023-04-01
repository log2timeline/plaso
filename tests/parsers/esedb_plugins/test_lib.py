# -*- coding: utf-8 -*-
"""ESEDB plugin related functions and classes for testing."""

from plaso.containers import events
from plaso.parsers import esedb
from plaso.parsers import mediator as parsers_mediator

from tests.parsers import test_lib


class ESEDBPluginTestCase(test_lib.ParserTestCase):
  """ESE database-based plugin test case."""

  def _ParseESEDBFileWithPlugin(self, path_segments, plugin):
    """Parses a file as an ESE database file and returns an event generator.

    This method will first test if an ESE database contains the required tables
    using plugin.CheckRequiredTables() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (ESEDBPlugin): ESE database plugin.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    parser_mediator = parsers_mediator.ParserMediator()

    storage_writer = self._CreateStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator.SetFileEntry(file_entry)

    if file_entry:
      event_data_stream = events.EventDataStream()
      event_data_stream.path_spec = file_entry.path_spec

      parser_mediator.ProduceEventDataStream(event_data_stream)

    # AppendToParserChain needs to be run after SetFileEntry.
    parser_mediator.AppendToParserChain('esedb')

    file_object = file_entry.GetFileObject()

    database = esedb.ESEDatabase()
    database.Open(file_object)

    try:
      required_tables_exist = plugin.CheckRequiredTables(database)
      self.assertTrue(required_tables_exist)

      cache = esedb.ESEDBCache()
      plugin.UpdateChainAndProcess(
          parser_mediator, cache=cache, database=database)

    finally:
      database.Close()

    return storage_writer
