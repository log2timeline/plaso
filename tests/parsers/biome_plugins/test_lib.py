# -*- coding: utf-8 -*-
"""Apple biome file plugin related functions and classes for testing."""

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import apple_biome

from tests.parsers import test_lib


class AppleBiomeTestCase(test_lib.ParserTestCase):
  """Apple biome plugin test case."""
  def _OpenAppleBiomeFile(self, path_segments):
    """Opens an Apple biome log file.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
    Returns:
      AppleBiomeFile: Apple biome file.
    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    file_entry = self._GetTestFileEntry(path_segments)

    file_object = file_entry.GetFileObject()

    apple_biome_file = apple_biome.AppleBiomeFile()
    apple_biome_file.Open(file_object)

    return apple_biome_file

  def _ParseAppleBiomeFileWithPlugin(self, path_segments, plugin):
    """Parses a file as an Apple biome file and returns an event generator. This
    method will first test if the Apple biome file has the required schema using
    plugin.CheckRequiredSchema() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (AppleBiomePlugin): Apple biome file plugin.
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
    parser_mediator.AppendToParserChain('apple_biome')

    biome_file = self._OpenAppleBiomeFile(path_segments)

    result = False
    for record in biome_file.records:
      result = plugin.CheckRequiredSchema(record.protobuf)
      if result:
        break

    self.assertTrue(result)

    plugin.UpdateChainAndProcess(parser_mediator, biome_file=biome_file)

    return storage_writer
