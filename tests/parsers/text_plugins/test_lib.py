# -*- coding: utf-8 -*-
"""Text parser plugin related functions and classes for testing."""

from dfvfs.helpers import text_file

from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class TextPluginTestCase(test_lib.ParserTestCase):
  """Text parser plugin test case."""

  def _ParseTextFileWithPlugin(
      self, path_segments, plugin, knowledge_base_values=None):
    """Parses a file as a text log file and returns an event generator.

    This method will first test if a text log file has the required format
    using plugin.CheckRequiredFormat() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (TextPlugin): text log file plugin.
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

    # TODO: add support for multiple lines.
    line = text_file_object.readline()

    required_format = plugin.CheckRequiredFormat([line])
    self.assertTrue(required_format)

    parser_mediator.AppendToParserChain('text')
    plugin.UpdateChainAndProcess(parser_mediator, file_object=file_object)

    return storage_writer
