# -*- coding: utf-8 -*-
"""JSON-L parser plugin related functions and classes for testing."""

import json

from dfvfs.helpers import text_file

from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class JSONLPluginTestCase(test_lib.ParserTestCase):
  """JSON-L parser plugin test case."""

  def _ParseJSONLFileWithPlugin(
      self, path_segments, plugin, knowledge_base_values=None):
    """Parses a file as an JSON-L log file and returns an event generator.

    This method will first test if a JSON-L log file has the required format
    using plugin.CheckRequiredFormat() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (JSONLPlugin): JSON-L log file plugin.
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
    text_file_object = text_file.TextFile(file_object)

    line = text_file_object.readline()
    json_dict = json.loads(line)

    required_format = plugin.CheckRequiredFormat(json_dict)
    self.assertTrue(required_format)

    plugin.Process(parser_mediator, file_object=file_object)

    return storage_writer
