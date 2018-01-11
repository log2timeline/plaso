# -*- coding: utf-8 -*-
"""ESEDB plugin related functions and classes for testing."""

from __future__ import unicode_literals

import pyesedb

from plaso.containers import sessions
from plaso.parsers import esedb
from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class ESEDBPluginTestCase(test_lib.ParserTestCase):
  """ESE database-based plugin test case."""

  def _ParseESEDBFileWithPlugin(
      self, path_segments, plugin, knowledge_base_values=None):
    """Parses a file as an ESE database file and returns an event generator.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (ESEDBPlugin): ESE database plugin.
      knowledge_base_values (Optional[dict[str, object]]): knowledge base
          values.

    Returns:
      FakeStorageWriter: storage writer.
    """
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=file_entry,
        knowledge_base_values=knowledge_base_values)

    file_object = file_entry.GetFileObject()

    try:
      esedb_file = pyesedb.file()
      esedb_file.open_file_object(file_object)
      cache = esedb.ESEDBCache()
      plugin.Process(parser_mediator, cache=cache, database=esedb_file)
      esedb_file.close()

    finally:
      file_object.close()

    return storage_writer
