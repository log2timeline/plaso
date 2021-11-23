# -*- coding: utf-8 -*-
"""Compound ZIP file plugin related functions and classes for testing."""

import zipfile

from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class CompoundZIPPluginTestCase(test_lib.ParserTestCase):
  """Compound ZIP file plugin test case."""

  def _ParseZIPFileWithPlugin(
      self, path_segments, plugin, knowledge_base_values=None):
    """Parses a file as a ZIP file and returns an event generator.

    This method will first test if a ZIP file contains the required paths
    using plugin.CheckRequiredPaths() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (CompoundZIPPlugin): compound ZIP file plugin.
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

    with zipfile.ZipFile(file_object, 'r', allowZip64=True) as zip_file:
      required_paths_exist = plugin.CheckRequiredPaths(zip_file)
      self.assertTrue(required_paths_exist)

      plugin.Process(parser_mediator, zip_file=zip_file)

    return storage_writer
