# -*- coding: utf-8 -*-
"""OLECF plugin related functions and classes for testing."""

import pyolecf

from plaso.engine import single_process
from plaso.parsers import test_lib


class OleCfPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for OLE CF based plugins."""

  def _OpenOleCfFile(self, path, codepage='cp1252'):
    """Opens an OLE compound file and returns back a pyolecf.file object.

    Args:
      path: The path to the OLE CF test file.
      codepage: Optional codepage. The default is cp1252.
    """
    file_entry = self._GetTestFileEntryFromPath([path])

    file_object = file_entry.GetFileObject()
    olecf_file = pyolecf.file()
    olecf_file.set_ascii_codepage(codepage)

    olecf_file.open_file_object(file_object)

    return olecf_file

  def _ParseOleCfFileWithPlugin(
      self, path, plugin_object, knowledge_base_values=None):
    """Parses a file as an OLE compound file and returns an event generator.

    Args:
      path: The path to the OLE CF test file.
      plugin_object: The plugin object that is used to extract an event
                     generator.
      knowledge_base_values: optional dict containing the knowledge base
                             values. The default is None.

    Returns:
      An event object queue consumer object (instance of
      TestItemQueueConsumer).
    """
    event_queue = single_process.SingleProcessQueue()
    event_queue_consumer = test_lib.TestItemQueueConsumer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()

    parser_mediator = self._GetParserMediator(
        event_queue, parse_error_queue,
        knowledge_base_values=knowledge_base_values)
    olecf_file = self._OpenOleCfFile(path)

    file_entry = self._GetTestFileEntryFromPath([path])
    parser_mediator.SetFileEntry(file_entry)

    # Get a list of all root items from the OLE CF file.
    root_item = olecf_file.root_item
    item_names = [item.name for item in root_item.sub_items]

    plugin_object.Process(
        parser_mediator, root_item=root_item, item_names=item_names)

    return event_queue_consumer
