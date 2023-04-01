# -*- coding: utf-8 -*-
"""Plist plugin related functions and classes for testing."""

import plistlib

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator

from tests.parsers import test_lib


class PlistPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for a plist plugin."""

  def _ParsePlistFileWithPlugin(self, plugin, path_segments, plist_name):
    """Parses a file using the parser and plugin object.

    Args:
      plugin (PlistPlugin): a plist plugin.
      path_segments (list[str]): the path segments inside the test data
          directory to the test file.
      plist_name (str): name of the plist to parse.

    Returns:
      FakeStorageWriter: a storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    file_entry = self._GetTestFileEntry(path_segments)
    file_object = file_entry.GetFileObject()

    top_level_object = plistlib.load(file_object)
    self.assertIsNotNone(top_level_object)

    return self._ParsePlistWithPlugin(plugin, plist_name, top_level_object)

  def _ParsePlistWithPlugin(
      self, plugin, plist_name, top_level_object, file_entry=None):
    """Parses a plist using the plugin object.

    Args:
      plugin (PlistPlugin): a plist plugin.
      plist_name (str): name of the plist to parse.
      top_level_object (dict[str, object]): plist top-level key.
      file_entry (Optional[dfvfs.FileEntry]): file entry.

    Returns:
      FakeStorageWriter: a storage writer.
    """
    parser_mediator = parsers_mediator.ParserMediator()

    storage_writer = self._CreateStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    parser_mediator.SetFileEntry(file_entry)

    if file_entry:
      event_data_stream = events.EventDataStream()
      event_data_stream.path_spec = file_entry.path_spec

      parser_mediator.ProduceEventDataStream(event_data_stream)

    # AppendToParserChain needs to be run after SetFileEntry.
    parser_mediator.AppendToParserChain('plist')

    plugin.UpdateChainAndProcess(
        parser_mediator, plist_name=plist_name, top_level=top_level_object)

    return storage_writer
