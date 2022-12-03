# -*- coding: utf-8 -*-
"""Compound ZIP file plugin related functions and classes for testing."""

import zipfile

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator

from tests.parsers import test_lib


class CompoundZIPPluginTestCase(test_lib.ParserTestCase):
  """Compound ZIP file plugin test case."""

  def _ParseZIPFileWithPlugin(
      self, path_segments, plugin, knowledge_base_values=None,
      time_zone_string=None):
    """Parses a file as a ZIP file and returns an event generator.

    This method will first test if a ZIP file contains the required paths
    using plugin.CheckRequiredPaths() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (CompoundZIPPlugin): compound ZIP file plugin.
      knowledge_base_values (Optional[dict[str, object]]): knowledge base
          values.
      time_zone_string (Optional[str]): time zone.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    # TODO: move knowledge base time_zone_string into knowledge_base_values.
    knowledge_base_object = self._CreateKnowledgeBase(
        knowledge_base_values=knowledge_base_values,
        time_zone_string=time_zone_string)

    parser_mediator = parsers_mediator.ParserMediator(knowledge_base_object)

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
