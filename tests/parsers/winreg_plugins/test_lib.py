# -*- coding: utf-8 -*-
"""Windows Registry plugin related functions and classes for testing."""

from dfvfs.path import fake_path_spec

from dfwinreg import fake as dfwinreg_fake
from dfwinreg import regf as dfwinreg_regf
from dfwinreg import registry as dfwinreg_registry

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator

from tests.parsers import test_lib


class TestFileEntry(object):
  """File entry object for testing purposes.

  Attributes:
    name (str): name of the file entry.
    path_spec (dfvfs.PathSpec): path specification of the file entry.
  """

  def __init__(self, name):
    """Initializes a file entry.

    Args:
      name (str): the file entry name.
    """
    super(TestFileEntry, self).__init__()
    self.name = name
    self.path_spec = fake_path_spec.FakePathSpec(location=name)


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

    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage='cp1252', emulate_virtual_keys=False)
    registry_file.Open(file_object)

    win_registry = dfwinreg_registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    return win_registry

  def _ParseKeyWithPlugin(self, registry_key, plugin, file_entry=None):
    """Parses a key within a Windows Registry file using the plugin.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry Key.
      plugin (WindowsRegistryPlugin): Windows Registry plugin.
      file_entry (Optional[dfvfs.FileEntry]): file entry.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    self.assertIsNotNone(registry_key)

    parser_mediator = parsers_mediator.ParserMediator()

    storage_writer = self._CreateStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    parser_mediator.SetFileEntry(file_entry)

    if file_entry:
      event_data_stream = events.EventDataStream()
      event_data_stream.path_spec = file_entry.path_spec

      parser_mediator.ProduceEventDataStream(event_data_stream)

    # AppendToParserChain needs to be run after SetFileEntry.
    parser_mediator.AppendToParserChain('winreg')

    plugin.UpdateChainAndProcess(parser_mediator, registry_key)

    return storage_writer
