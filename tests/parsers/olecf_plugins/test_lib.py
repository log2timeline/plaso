# -*- coding: utf-8 -*-
"""OLECF plugin related functions and classes for testing."""

import pyolecf

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator

from tests.parsers import test_lib


class OLECFPluginTestCase(test_lib.ParserTestCase):
  """OLE CF-based plugin test case."""

  # pylint: disable=no-member

  def _ParseOLECFFileWithPlugin(
      self, path_segments, plugin, codepage='cp1252',
      knowledge_base_values=None, time_zone_string=None):
    """Parses a file as an OLE compound file and returns an event generator.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (OLECFPlugin): OLE CF plugin.
      codepage (Optional[str]): codepage.
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
    parser_mediator.AppendToParserChain('olecf')

    file_object = file_entry.GetFileObject()

    olecf_file = pyolecf.file()
    olecf_file.set_ascii_codepage(codepage)
    olecf_file.open_file_object(file_object)

    try:
      # Get a list of all root items from the OLE CF file.
      root_item = olecf_file.root_item
      item_names = [item.name for item in root_item.sub_items]

      plugin.UpdateChainAndProcess(
          parser_mediator, root_item=root_item, item_names=item_names)

    finally:
      olecf_file.close()

    return storage_writer
