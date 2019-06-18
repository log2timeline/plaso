# -*- coding: utf-8 -*-
"""Windows Registry plugin related functions and classes for testing."""

from __future__ import unicode_literals

from dfwinreg import fake as dfwinreg_fake
from dfwinreg import registry as dfwinreg_registry

from plaso.containers import sessions
from plaso.parsers import winreg
from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class RegistryPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for a Windows Registry plugin."""

  # pylint: disable=protected-access

  def _AssertFiltersOnKeyPath(self, plugin, key_path):
    """Asserts if the key path matches one of the plugin filters.

    Args:
      plugin (WindowsRegistryPlugin): Windows Registry plugin.
      key_path (str): Windows Registry key path.
    """
    _, _, key_name = key_path.rpartition('\\')
    registry_key = dfwinreg_fake.FakeWinRegistryKey(key_name, key_path=key_path)

    result = self._CheckFiltersOnKeyPath(plugin, registry_key)
    self.assertTrue(result)

  def _AssertNotFiltersOnKeyPath(self, plugin, key_path):
    """Asserts if the key path does not match one of the plugin filters.

    Args:
      plugin (WindowsRegistryPlugin): Windows Registry plugin.
      key_path (str): Windows Registry key path.
    """
    _, _, key_name = key_path.rpartition('\\')
    registry_key = dfwinreg_fake.FakeWinRegistryKey(key_name, key_path=key_path)

    result = self._CheckFiltersOnKeyPath(plugin, registry_key)
    self.assertFalse(result)

  def _CheckFiltersOnKeyPath(self, plugin, registry_key):
    """Checks if the key path matches one of the plugin filters.

    Args:
      plugin (WindowsRegistryPlugin): Windows Registry plugin.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      bool: True if the key path matches one of the plugin filters,
          False otherwise.
    """
    result = False
    for path_filter in plugin.FILTERS:
      if path_filter.Match(registry_key):
        result = True

    return result

  def _GetWinRegistryFromFileEntry(self, file_entry):
    """Retrieves a Windows Registry from a file entry.

    Args:
      file_entry (dfvfs.FileEntry): file entry that references a test file.

    Returns:
      dfwinreg.WinRegistry: Windows Registry or None.
    """
    file_object = file_entry.GetFileObject()
    if not file_object:
      return None

    win_registry_reader = winreg.FileObjectWinRegistryFileReader()
    registry_file = win_registry_reader.Open(file_object)
    if not registry_file:
      file_object.close()
      return None

    win_registry = dfwinreg_registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    return win_registry

  def _ParseKeyWithPlugin(
      self, registry_key, plugin, file_entry=None, knowledge_base_values=None,
      parser_chain=None):
    """Parses a key within a Windows Registry file using the plugin.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry Key.
      plugin (WindowsRegistryPlugin): Windows Registry plugin.
      file_entry (Optional[dfvfs.FileEntry]): file entry.
      knowledge_base_values (Optional[dict[str, str]]): knowledge base values.
      parser_chain (Optional[str]): parsing chain up to this point.

    Returns:
      FakeStorageWriter: storage writer.
    """
    self.assertNotEqual(registry_key, None)

    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=file_entry,
        knowledge_base_values=knowledge_base_values)

    # Most tests aren't explicitly checking for parser chain values,
    # or setting them, so we'll just append the plugin name if no explicit
    # parser chain argument is supplied.
    if parser_chain is None:
      # AppendToParserChain needs to be run after SetFileEntry.
      parser_mediator.AppendToParserChain(plugin)

    else:
      # In the rare case that a test is checking for a particular chain, we
      # provide a way set it directly. There's no public API for this,
      # as access to the parser chain should be very infrequent.
      parser_mediator._parser_chain_components = parser_chain.split('/')

    plugin.Process(parser_mediator, registry_key)

    return storage_writer
