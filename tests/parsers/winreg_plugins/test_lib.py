# -*- coding: utf-8 -*-
"""Windows Registry plugin related functions and classes for testing."""

from plaso.dfwinreg import registry as dfwinreg_registry
from plaso.engine import single_process
from plaso.parsers import winreg

from tests.parsers import test_lib


class RegistryPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for a Windows Registry plugin."""

  def _GetWinRegistryFromFileEntry(self, file_entry):
    """Retrieves a Windows Registry from a file entry.

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry) that
                  references a test file.

    Returns:
      A Windows Registry object (instance of dfwinreg.WinRegistry) or None.
    """
    file_object = file_entry.GetFileObject()
    if not file_object:
      return

    win_registry_reader = winreg.FileObjectWinRegistryFileReader()
    registry_file = win_registry_reader.Open(file_object)
    if not registry_file:
      file_object.close()
      return

    win_registry = dfwinreg_registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    return win_registry

  def _ParseKeyWithPlugin(
      self, plugin_object, registry_key, file_entry=None,
      knowledge_base_values=None, parser_chain=None):
    """Parses a key within a Windows Registry file using the plugin object.

    Args:
      plugin_object: The plugin object.
      registry_key: The Windows Registry Key.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
      knowledge_base_values: Optional dict containing the knowledge base
                             values.
      parser_chain: Optional string containing the parsing chain up to this
                    point.

    Returns:
      An event object queue consumer object (instance of
      TestItemQueueConsumer).
    """
    self.assertNotEqual(registry_key, None)

    event_queue = single_process.SingleProcessQueue()
    event_queue_consumer = test_lib.TestItemQueueConsumer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()

    parser_mediator = self._GetParserMediator(
        event_queue, parse_error_queue,
        knowledge_base_values=knowledge_base_values)

    parser_mediator.SetFileEntry(file_entry)

    # Most tests aren't explicitly checking for parser chain values,
    # or setting them, so we'll just append the plugin name if no explicit
    # parser chain argument is supplied.
    # pylint: disable=protected-access
    if parser_chain is None:
      # AppendToParserChain needs to be run after SetFileEntry.
      parser_mediator.AppendToParserChain(plugin_object)
    else:
      # In the rare case that a test is checking for a particular chain, we
      # provide a way set it directly. There's no public API for this,
      # as access to the parser chain should be very infrequent.
      parser_mediator._parser_chain_components = parser_chain.split(u'/')

    plugin_object.Process(parser_mediator, registry_key)

    return event_queue_consumer

  def _TestRegvalue(self, event_object, identifier, expected_value):
    """Tests a specific 'regvalue' attribute within the event object.

    Args:
      event_object: the event object (instance of EventObject).
      identifier: the identifier of the 'regvalue' attribute.
      expected_value: the expected value of the 'regvalue' attribute.
    """
    self.assertTrue(hasattr(event_object, u'regvalue'))
    self.assertIn(identifier, event_object.regvalue)
    self.assertEqual(event_object.regvalue[identifier], expected_value)
