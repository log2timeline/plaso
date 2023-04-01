# -*- coding: utf-8 -*-
"""JSON-L parser plugin related functions and classes for testing."""

import json

from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator

from tests.parsers import test_lib


class JSONLPluginTestCase(test_lib.ParserTestCase):
  """JSON-L parser plugin test case."""

  def _ParseJSONLFileWithPlugin(self, path_segments, plugin):
    """Parses a file as an JSON-L log file and returns an event generator.

    This method will first test if a JSON-L log file has the required format
    using plugin.CheckRequiredFormat() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (JSONLPlugin): JSON-L log file plugin.

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
    parser_mediator.AppendToParserChain('jsonl')

    file_object = file_entry.GetFileObject()
    text_file_object = text_file.TextFile(file_object)

    line = text_file_object.readline()
    json_dict = json.loads(line)

    required_format = plugin.CheckRequiredFormat(json_dict)
    self.assertTrue(required_format)

    plugin.UpdateChainAndProcess(parser_mediator, file_object=file_object)

    return storage_writer
