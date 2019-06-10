# -*- coding: utf-8 -*-
"""Plist plugin related functions and classes for testing."""

from __future__ import unicode_literals

from plaso.storage.fake import writer as fake_writer

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
      plugin (PlistPlugin): a plist plugin.
      path_segments (list[str]): the path segments inside the test data
          directory to the test file.
      plist_name (str): name of the plist to parse.
      knowledge_base_values (Optional[dict[str, object]]): knowledge base
          values.

    Returns:
      FakeStorageWriter: a storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
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
      plugin (PlistPlugin): a plist plugin.
      plist_name (str): name of the plist to parse.
      top_level_object (dict[str, object]): plist top-level key.
      knowledge_base_values (Optional[dict[str, object]]): knowledge base
          values.

    Returns:
      FakeStorageWriter: a storage writer.
    """
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    parser_mediator = self._CreateParserMediator(
        storage_writer, knowledge_base_values=knowledge_base_values)

    plugin.Process(
        parser_mediator, plist_name=plist_name, top_level=top_level_object)

    return storage_writer
