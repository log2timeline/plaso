# -*- coding: utf-8 -*-
"""OLECF plugin related functions and classes for testing."""

from __future__ import unicode_literals

import pyolecf

from plaso.containers import sessions
from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class OLECFPluginTestCase(test_lib.ParserTestCase):
  """OLE CF-based plugin test case."""

  # pylint: disable=no-member

  def _ParseOLECFFileWithPlugin(
      self, path_segments, plugin, codepage='cp1252',
      knowledge_base_values=None):
    """Parses a file as an OLE compound file and returns an event generator.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (OLECFPlugin): OLE CF plugin.
      codepage (Optional[str]): codepage.
      knowledge_base_values (Optional[dict[str, object]]): knowledge base
          values.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=file_entry,
        knowledge_base_values=knowledge_base_values)

    file_object = file_entry.GetFileObject()

    try:
      olecf_file = pyolecf.file()
      olecf_file.set_ascii_codepage(codepage)
      olecf_file.open_file_object(file_object)

      # Get a list of all root items from the OLE CF file.
      root_item = olecf_file.root_item
      item_names = [item.name for item in root_item.sub_items]

      plugin.Process(
          parser_mediator, root_item=root_item, item_names=item_names)

      olecf_file.close()

    finally:
      file_object.close()

    return storage_writer
