# -*- coding: utf-8 -*-
"""Parser for Windows NT Registry (REGF) files."""

import logging

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.winreg import cache
from plaso.winreg import winregistry


# TODO: add tests for this class.
class PluginList(object):
  """A simple class that stores information about Windows Registry plugins."""

  def __init__(self):
    """Initializes the plugin list object."""
    super(PluginList, self).__init__()
    self._key_plugins = {}
    self._value_plugins = {}

  def __iter__(self):
    """Return an iterator of all Windows Registry plugins."""
    ret = []
    _ = map(ret.extend, self._key_plugins.values())
    _ = map(ret.extend, self._value_plugins.values())
    for item in ret:
      yield item

  def _GetPluginsByType(self, plugins_dict, plugin_type):
    """Retrieves the Windows Registry plugins of a specific type.

    Args:
      plugins_dict: Dictionary containing the Windows Registry plugins
                    by plugin type.
      plugin_type: String containing the Windows Registry type,
                   e.g. NTUSER, SOFTWARE.

    Returns:
      A list containing the Windows Registry plugins (instances of
      RegistryPlugin) for the specific plugin type.
    """
    return plugins_dict.get(plugin_type, []) + plugins_dict.get(u'any', [])

  def AddPlugin(self, plugin_type, plugin_class):
    """Add a Windows Registry plugin to the plugin list.

    Args:
      plugin_type: String containing the Windows Registry type,
                   e.g. NTUSER, SOFTWARE.
      plugin_class: The plugin class that is being registered.
    """
    # Cannot import the interface here otherwise this will create a cyclic
    # dependency.
    if hasattr(plugin_class, u'REG_VALUES'):
      self._value_plugins.setdefault(plugin_type, []).append(plugin_class)

    else:
      self._key_plugins.setdefault(plugin_type, []).append(plugin_class)

  def GetAllKeyPlugins(self):
    """Return all key plugins as a list."""
    ret = []
    _ = map(ret.extend, self._key_plugins.values())
    return ret

  def GetAllValuePlugins(self):
    """Return a list of a all classes that implement value-based plugins."""
    ret = []
    _ = map(ret.extend, self._value_plugins.values())
    return ret

  def GetExpandedKeyPaths(
      self, parser_mediator, reg_cache=None, plugin_names=None):
    """Retrieves a list of expanded Windows Registry key paths.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      reg_cache: Optional Windows Registry objects cache (instance of
                 WinRegistryCache). The default is None.
      plugin_names: Optional list of plugin names, if defined only keys from
                    these plugins will be expanded. The default is None which
                    means all key plugins will get expanded keys.

    Returns:
      A list of expanded Windows Registry key paths.
    """
    key_paths = []
    for key_plugin_cls in self.GetAllKeyPlugins():
      key_plugin = key_plugin_cls(reg_cache=reg_cache)

      if plugin_names and key_plugin.NAME not in plugin_names:
        continue
      key_plugin.ExpandKeys(parser_mediator)
      if not key_plugin.expanded_keys:
        continue

      for key_path in key_plugin.expanded_keys:
        if key_path not in key_paths:
          key_paths.append(key_path)

    return key_paths

  def GetKeyPlugins(self, plugin_type):
    """Retrieves the Windows Registry key-based plugins of a specific type.

    Args:
      plugin_type: String containing the Windows Registry type,
                   e.g. NTUSER, SOFTWARE.

    Returns:
      A list containing the Windows Registry plugins (instances of
      RegistryPlugin) for the specific plugin type.
    """
    return self._GetPluginsByType(self._key_plugins, plugin_type)

  def GetTypes(self):
    """Return a set of all plugins supported."""
    return set(self._key_plugins).union(self._value_plugins)

  def GetValuePlugins(self, plugin_type):
    """Retrieves the Windows Registry value-based plugins of a specific type.

    Args:
      plugin_type: String containing the Windows Registry type,
                   e.g. NTUSER, SOFTWARE.

    Returns:
      A list containing the Windows Registry plugins (instances of
      RegistryPlugin) for the specific plugin type.
    """
    return self._GetPluginsByType(self._value_plugins, plugin_type)

  def GetWeights(self):
    """Return a set of all weights/priority of the loaded plugins."""
    return set(plugin.WEIGHT for plugin in self.GetAllValuePlugins()).union(
        plugin.WEIGHT for plugin in self.GetAllKeyPlugins())

  def GetWeightPlugins(self, weight, plugin_type=u''):
    """Return a list of all plugins for a given weight or priority.

    Each plugin defines a weight or a priority that defines in which order
    it should be processed in the case of a parser that applies priority.

    This method returns all plugins, whether they are key or value based
    that use a defined weight or priority and are defined to parse keys
    or values found in a certain Windows Registry type.

    Args:
      weight: An integer representing the weight or priority (usually a
      number from 1 to 3).
      plugin_type: A string that defines the Windows Registry type, eg. NTUSER,
      SOFTWARE, etc.

    Returns:
      A list that contains all the plugins that fit the defined criteria.
    """
    ret = []
    for reg_plugin in self.GetKeyPlugins(plugin_type):
      if reg_plugin.WEIGHT == weight:
        ret.append(reg_plugin)

    for reg_plugin in self.GetValuePlugins(plugin_type):
      if reg_plugin.WEIGHT == weight:
        ret.append(reg_plugin)

    return ret


class WinRegistryParser(interface.BasePluginsParser):
  """Parses Windows NT Registry (REGF) files."""

  NAME = u'winreg'
  DESCRIPTION = u'Parser for Windows NT Registry (REGF) files.'

  _plugin_classes = {}

  # List of types Windows Registry file types and required keys to identify
  # each of these types.
  _REGISTRY_FILE_TYPES = {
      u'NTUSER': (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer',),
      u'SOFTWARE': (u'\\Microsoft\\Windows\\CurrentVersion\\App Paths',),
      u'SECURITY': (u'\\Policy\\PolAdtEv',),
      u'SYSTEM': (u'\\Select',),
      u'SAM': (u'\\SAM\\Domains\\Account\\Users',),
      u'UNKNOWN': (),
  }

  def __init__(self):
    """Initializes a parser object."""
    super(WinRegistryParser, self).__init__()
    self._plugins = WinRegistryParser.GetPluginList()

  def _CheckSignature(self, parser_mediator):
    """Checks if the file matches the signature of a REGF file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Returns:
      A boolean value indicating if the file matches the signature of
      a REGF file.
    """
    file_object = parser_mediator.GetFileObject()
    try:
      data = file_object.read(4)
    finally:
      file_object.close()

    return data == b'regf'

  def _GetRegistryFileType(self, winreg_file):
    """Determines the Registry file type.

    Args:
      winreg_file: A Windows Registry file (instance of WinRegFile).

    Returns:
      The Registry file type.
    """
    registry_type = u'UNKNOWN'
    for reg_type in self._REGISTRY_FILE_TYPES:
      if reg_type == u'UNKNOWN':
        continue

      # Check if all the known keys for a certain Registry file exist.
      known_keys_found = True
      for known_key_path in self._REGISTRY_FILE_TYPES[reg_type]:
        if not winreg_file.GetKeyByPath(known_key_path):
          known_keys_found = False
          break

      if known_keys_found:
        registry_type = reg_type
        break

    return registry_type

  def _ParseRegistryFile(
      self, parser_mediator, winreg_file, registry_cache, registry_type):
    """Parses a Windows Registry file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      winreg_file: A Windows Registry file (instance of WinRegFile).
      registry_cache: The Registry cache object (instance of WinRegistryCache).
      registry_type: The Registry file type.
    """
    plugins = {}
    number_of_plugins = 0
    for weight in self._plugins.GetWeights():
      plist = self._plugins.GetWeightPlugins(weight, registry_type)
      plugins[weight] = []
      for plugin in plist:
        plugins[weight].append(plugin(reg_cache=registry_cache))
        number_of_plugins += 1

    logging.debug(
        u'Number of plugins for this Windows Registry file: {0:d}.'.format(
            number_of_plugins))

    # Recurse through keys in the file and apply the plugins in the order:
    # 1. file type specific key-based plugins.
    # 2. generic key-based plugins.
    # 3. file type specific value-based plugins.
    # 4. generic value-based plugins.
    root_key = winreg_file.GetKeyByPath(u'\\')

    for key in self._RecurseKey(root_key):
      for weight in iter(plugins.keys()):
        # TODO: determine if the plugin matches the key and continue
        # to the next key.
        for plugin in plugins[weight]:
          if parser_mediator.abort:
            break

          plugin.UpdateChainAndProcess(
              parser_mediator, key=key, registry_type=registry_type,
              codepage=parser_mediator.codepage)

  def _RecurseKey(self, key):
    """A generator that takes a key and yields every subkey of it."""
    # In the case of a Registry file not having a root key we will not be able
    # to traverse the Registry, in which case we need to return here.
    if not key:
      return

    yield key

    for subkey in key.GetSubkeys():
      for recursed_key in self._RecurseKey(subkey):
        yield recursed_key

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

  def Parse(self, parser_mediator, **kwargs):
    """Parses a Windows Registry file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    display_name = parser_mediator.GetDisplayName()

    # TODO: Remove this magic reads when the classifier has been
    # implemented, until then we need to make sure we are dealing with
    # a Windows NT Registry file before proceeding.

    if not self._CheckSignature(parser_mediator):
      raise errors.UnableToParseFile((
          u'[{0:s}] unable to parse file: {1:s} with error: invalid '
          u'signature.').format(self.NAME, display_name))

    # TODO: refactor this.
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    file_entry = parser_mediator.GetFileEntry()
    try:
      winreg_file = registry.OpenFile(
          file_entry, codepage=parser_mediator.codepage)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, display_name, exception))

    try:
      registry_type = self._GetRegistryFileType(winreg_file)
      logging.debug(
          u'Windows Registry file {0:s}: detected as: {1:s}'.format(
              display_name, registry_type))

      registry_cache = cache.WinRegistryCache()
      registry_cache.BuildCache(winreg_file, registry_type)

      self._ParseRegistryFile(
          parser_mediator, winreg_file, registry_cache, registry_type)

    finally:
      winreg_file.Close()


manager.ParsersManager.RegisterParser(WinRegistryParser)
