# -*- coding: utf-8 -*-
"""Compound ZIP file plugin related functions and classes for testing."""

import zipfile

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator

from tests.parsers import test_lib


class CompoundZIPPluginTestCase(test_lib.ParserTestCase):
  """Compound ZIP file plugin test case."""

  def _ParseZIPFileWithPlugin(self, path_segments, plugin):
    """Parses a file as a ZIP file and returns an event generator.

    This method will first test if a ZIP file contains the required paths
    using plugin.CheckRequiredPaths() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (CompoundZIPPlugin): compound ZIP file plugin.

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
    parser_mediator.AppendToParserChain('czip')

    file_object = file_entry.GetFileObject()

    with zipfile.ZipFile(file_object, 'r', allowZip64=True) as zip_file:
      required_paths_exist = plugin.CheckRequiredPaths(zip_file)
      self.assertTrue(required_paths_exist)

      plugin.UpdateChainAndProcess(parser_mediator, zip_file=zip_file)

    return storage_writer
