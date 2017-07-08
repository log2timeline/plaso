# -*- coding: utf-8 -*-
"""Plist plugin related functions and classes for testing."""

from plaso.storage import fake_storage

from plaso.containers import sessions
from plaso.parsers import plist
from tests.parsers import test_lib


class PlistPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for a plist plugin."""

  def _ParsePlistFileWithPlugin(
      self, plugin, path_segments, plist_name,
      knowledge_base_values=None):
    """Parses a file using the parser and plugin object.

    Args:
      plugin: a plist plugin object (instance of PlistPlugin).
      path_segments: the path segments inside the test data directory to the
                     test file.
      plist_name: the name of the plist to parse.
      knowledge_base_values: optional dict containing the knowledge base
                             values.

    Returns:
      A storage writer object (instance of FakeStorageWriter).
    """
    file_entry = self._GetTestFileEntry(path_segments)
    file_object = file_entry.GetFileObject()

    parser = plist.PlistParser()
    top_level_object = parser.GetTopLevel(file_object)
    self.assertIsNotNone(top_level_object)

    return self._ParsePlistWithPlugin(
        plugin, plist_name, top_level_object,
        knowledge_base_values=knowledge_base_values)

  def _ParsePlistWithPlugin(
      self, plugin, plist_name, top_level_object,
      knowledge_base_values=None):
    """Parses a plist using the plugin object.

    Args:
      plugin: a plist plugin object (instance of PlistPlugin).
      plist_name: a string containg the name of the plist to parse.
      top_level_object: the top-level plist object.
      knowledge_base_values: optional dict containing the knowledge base
                             values.

    Returns:
      A storage writer object (instance of FakeStorageWriter).
    """
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    parser_mediator = self._CreateParserMediator(
        storage_writer, knowledge_base_values=knowledge_base_values)

    plugin.Process(
        parser_mediator, plist_name=plist_name, top_level=top_level_object)

    return storage_writer
