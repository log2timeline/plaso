# -*- coding: utf-8 -*-
"""Parser for Windows NT Registry (REGF) files."""

import logging

from plaso.dfwinreg import regf as dfwinreg_regf
from plaso.dfwinreg import registry as dfwinreg_registry
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


# TODO: add tests for this class.
class PluginList(object):
  """A simple class that stores information about Windows Registry plugins."""

  def __init__(self):
    """Initializes the plugin list object."""
    super(PluginList, self).__init__()
    self._plugins = {}

  def __iter__(self):
    """Return an iterator of all Windows Registry plugins."""
    ret = []
    _ = map(ret.extend, self._plugins.values())
    for item in ret:
      yield item

  def _GetPluginsByType(self, plugins_dict, registry_file_type):
    """Retrieves the Windows Registry plugins of a specific type.

    Args:
      plugins_dict: Dictionary containing the Windows Registry plugins
                    by plugin type.
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.

    Returns:
      A list containing the Windows Registry plugins (instances of
      RegistryPlugin) for the specific plugin type.
    """
    return plugins_dict.get(
        registry_file_type, []) + plugins_dict.get(u'any', [])

  def AddPlugin(self, registry_file_type, plugin_class):
    """Add a Windows Registry plugin to the plugin list.

    Args:
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.
      plugin_class: The plugin class that is being registered.
    """
    self._plugins.setdefault(registry_file_type, []).append(plugin_class)

  def GetAllPlugins(self):
    """Return all key plugins as a list."""
    ret = []
    _ = map(ret.extend, self._plugins.values())
    return ret

  def GetExpandedKeyPaths(self, parser_mediator, plugin_names=None):
    """Retrieves a list of expanded Windows Registry key paths.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      plugin_names: Optional list of plugin names, if defined only keys from
                    these plugins will be expanded. The default is None which
                    means all key plugins will get expanded keys.

    Returns:
      A list of expanded Windows Registry key paths.
    """
    key_paths = []
    for plugin_cls in self.GetAllPlugins():
      plugin_object = plugin_cls()

      if plugin_names and plugin_object.NAME not in plugin_names:
        continue
      plugin_object.ExpandKeys(parser_mediator)
      if not plugin_object.expanded_keys:
        continue

      for key_path in plugin_object.expanded_keys:
        if key_path not in key_paths:
          key_paths.append(key_path)

    return key_paths

  def GetPluginObjectByName(self, registry_file_type, plugin_name):
    """Creates a new instance of a specific Windows Registry plugin.

    Args:
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.
      plugin_name: the name of the plugin.

    Returns:
      The Windows Registry plugin (instance of RegistryPlugin) or None.
    """
    # TODO: make this a dict lookup instead of a list iteration.
    for plugin_cls in self.GetPlugins(registry_file_type):
      if plugin_cls.NAME == plugin_name:
        return plugin_cls()

  def GetPluginObjects(self, registry_file_type):
    """Creates new instances of a specific type of Windows Registry plugins.

    Args:
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.

    Returns:
      The Windows Registry plugin (instance of RegistryPlugin) or None.
    """
    return [plugin_cls() for plugin_cls in self.GetPlugins(registry_file_type)]

  def GetPlugins(self, registry_file_type):
    """Retrieves the Windows Registry key-based plugins of a specific type.

    Args:
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.

    Returns:
      A list containing the Windows Registry plugins (types of
      RegistryPlugin) for the specific plugin type.
    """
    return self._GetPluginsByType(self._plugins, registry_file_type)

  def GetTypes(self):
    """Return a set of all plugins supported."""
    return set(self._plugins)


class WinRegistryParser(interface.SingleFileBaseParser):
  """Parses Windows NT Registry (REGF) files."""

  NAME = u'winreg'
  DESCRIPTION = u'Parser for Windows NT Registry (REGF) files.'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(WinRegistryParser, self).__init__()
    self._plugins = WinRegistryParser.GetPluginList()
    self._win_registry = dfwinreg_registry.WinRegistry(
        backend=dfwinreg_registry.WinRegistry.BACKEND_PYREGF)

  def _ParseRegistryFile(
      self, parser_mediator, winreg_file, registry_file_type):
    """Parses a Windows Registry file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      winreg_file: A Windows Registry file (instance of
                   dfwinreg.WinRegistryFile).
      registry_file_type: The Registry file type.
    """
    plugins = self._plugins.GetPluginObjects(registry_file_type)
    logging.debug(
        u'Number of plugins for this Windows Registry file: {0:d}.'.format(
            len(plugins)))

    # Recurse through keys in the file and apply the plugins in the order:
    # 1. file type specific plugins.
    # 2. generic plugins.

    for key in winreg_file.RecurseKeys():
      for plugin_object in plugins:
        # TODO: determine if the plugin matches the key and continue
        # to the next key.
        if parser_mediator.abort:
          break

        plugin_object.UpdateChainAndProcess(
            parser_mediator, key=key, registry_file_type=registry_file_type,
            codepage=parser_mediator.codepage)

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'regf', offset=0)
    return format_specification

  @classmethod
  def GetPluginList(cls):
    """Build a list of all available plugins.

    Returns:
      A plugins list (instance of PluginList).
    """
    plugins_list = PluginList()
    for _, plugin_class in cls.GetPlugins():
      plugins_list.AddPlugin(plugin_class.REG_TYPE, plugin_class)
    return plugins_list

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows Registry file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    display_name = parser_mediator.GetDisplayName()

    winreg_file = dfwinreg_regf.WinRegistryFileREGF(
        ascii_codepage=parser_mediator.codepage)

    try:
      winreg_file.Open(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, display_name, exception))

    registry_file_type = self._win_registry.GetRegistryFileType(winreg_file)
    logging.debug(
        u'Windows Registry file {0:s}: detected as: {1:s}'.format(
            display_name, registry_file_type))

    self._ParseRegistryFile(parser_mediator, winreg_file, registry_file_type)


manager.ParsersManager.RegisterParser(WinRegistryParser)
