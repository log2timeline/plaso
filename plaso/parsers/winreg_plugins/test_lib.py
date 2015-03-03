# -*- coding: utf-8 -*-
"""Windows Registry plugin related functions and classes for testing."""

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import single_process
from plaso.parsers import test_lib
from plaso.winreg import winregistry


class RegistryPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for a Windows Registry plugin."""

  def _GetKeyFromFile(self, path, key_path):
    """Retrieves a Windows Registry key from a file.

    Args:
      path: The path to the file, as a string.
      key_path: The path of the key to parse.

    Returns:
      A Windows Registry key (instance of WinRegKey).
    """
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    return self._GetKeyFromFileEntry(file_entry, key_path)

  def _GetKeyFromFileEntry(self, file_entry, key_path):
    """Retrieves a Windows Registry key from a file.

    Args:
      file_entry: A dfVFS file_entry object that references a test file.
      key_path: The path of the key to parse.

    Returns:
      A Windows Registry key (instance of WinRegKey).
    """
    registry = winregistry.WinRegistry(winregistry.WinRegistry.BACKEND_PYREGF)
    winreg_file = registry.OpenFile(file_entry, codepage='cp1252')
    return winreg_file.GetKeyByPath(key_path)

  def _ParseKeyWithPlugin(
      self, plugin_object, winreg_key, knowledge_base_values=None,
      file_entry=None, parser_chain=None):
    """Parses a key within a Windows Registry file using the plugin object.

    Args:
      plugin_object: The plugin object.
      winreg_key: The Windows Registry Key.
      knowledge_base_values: Optional dict containing the knowledge base
                             values. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.

    Returns:
      An event object queue consumer object (instance of
      TestEventObjectQueueConsumer).
    """
    self.assertNotEquals(winreg_key, None)

    event_queue = single_process.SingleProcessQueue()
    event_queue_consumer = test_lib.TestEventObjectQueueConsumer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()

    parser_mediator = self._GetParserMediator(
        event_queue, parse_error_queue,
        knowledge_base_values=knowledge_base_values)

    # Most tests aren't explicitly checking for parser chain values,
    # or setting them, so we'll just append the plugin name if no explicit
    # parser chain argument is supplied.
    # pylint: disable=protected-access
    if parser_chain is None:
      parser_mediator.AppendToParserChain(plugin_object)
    else:
      # In the rare case that a test is checking for a particular chain, we
      # provide a way set it directly. There's no public API for this,
      # as access to the parser chain should be very infrequent.
      parser_mediator._parser_chain_components = parser_chain.split(u'/')

    parser_mediator.SetFileEntry(file_entry)

    plugin_object.Process(parser_mediator, key=winreg_key)

    return event_queue_consumer

  def _TestRegvalue(self, event_object, identifier, expected_value):
    """Tests a specific 'regvalue' attribute within the event object.

    Args:
      event_object: the event object (instance of EventObject).
      identifier: the identifier of the 'regvalue' attribute.
      expected_value: the expected value of the 'regvalue' attribute.
    """
    self.assertTrue(hasattr(event_object, 'regvalue'))
    self.assertIn(identifier, event_object.regvalue)
    self.assertEqual(event_object.regvalue[identifier], expected_value)
