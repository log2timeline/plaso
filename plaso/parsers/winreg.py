# -*- coding: utf-8 -*-
"""Parser for Windows NT Registry (REGF) files."""

import logging

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
    self._key_plugins = {}
    self._value_plugins = {}

  def __iter__(self):
    """Return an iterator of all Windows Registry plugins."""
    ret = []
    _ = map(ret.extend, self._key_plugins.values())
    _ = map(ret.extend, self._value_plugins.values())
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
    # Cannot import the interface here otherwise this will create a cyclic
    # dependency.
    if hasattr(plugin_class, u'REG_VALUES'):
      self._value_plugins.setdefault(
          registry_file_type, []).append(plugin_class)

    else:
      self._key_plugins.setdefault(registry_file_type, []).append(plugin_class)

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
    for key_plugin_cls in self.GetAllKeyPlugins():
      key_plugin = key_plugin_cls()

      if plugin_names and key_plugin.NAME not in plugin_names:
        continue
      key_plugin.ExpandKeys(parser_mediator)
      if not key_plugin.expanded_keys:
        continue

      for key_path in key_plugin.expanded_keys:
        if key_path not in key_paths:
          key_paths.append(key_path)

    return key_paths

  def GetKeyPluginByName(self, registry_file_type, plugin_name):
    """Retrieves a Windows Registry key-based plugin for a specific name.

    Args:
      registry_file_type: string containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.
      plugin_name: the name of the plugin.

    Returns:
      The Windows Registry plugin (instance of RegistryPlugin) or None.
    """
    # TODO: make this a dict lookup instead of a list iteration.
    for plugin_cls in self.GetKeyPlugins(registry_file_type):
      if plugin_cls.NAME == plugin_name:
        return plugin_cls()

  def GetKeyPlugins(self, registry_file_type):
    """Retrieves the Windows Registry key-based plugins of a specific type.

    Args:
      registry_file_type: string containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.

    Returns:
      A list containing the Windows Registry plugins (instances of
      RegistryPlugin) for the specific plugin type.
    """
    return self._GetPluginsByType(self._key_plugins, registry_file_type)

  def GetTypes(self):
    """Return a set of all plugins supported."""
    return set(self._key_plugins).union(self._value_plugins)

  def GetValuePlugins(self, registry_file_type):
    """Retrieves the Windows Registry value-based plugins of a specific type.

    Args:
      registry_file_type: string containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.

    Returns:
      A list containing the Windows Registry plugins (instances of
      RegistryPlugin) for the specific plugin type.
    """
    return self._GetPluginsByType(self._value_plugins, registry_file_type)

  def GetWeights(self):
    """Return a set of all weights/priority of the loaded plugins."""
    return set(plugin.WEIGHT for plugin in self.GetAllValuePlugins()).union(
        plugin.WEIGHT for plugin in self.GetAllKeyPlugins())

  def GetWeightPlugins(self, weight, registry_file_type=u''):
    """Return a list of all plugins for a given weight or priority.

    Each plugin defines a weight or a priority that defines in which order
    it should be processed in the case of a parser that applies priority.

    This method returns all plugins, whether they are key or value based
    that use a defined weight or priority and are defined to parse keys
    or values found in a certain Windows Registry type.

    Args:
      weight: An integer representing the weight or priority (usually a
              number from 1 to 3).
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.

    Returns:
      A list that contains all the plugins that fit the defined criteria.
    """
    ret = []
    for reg_plugin in self.GetKeyPlugins(registry_file_type):
      if reg_plugin.WEIGHT == weight:
        ret.append(reg_plugin)

    for reg_plugin in self.GetValuePlugins(registry_file_type):
      if reg_plugin.WEIGHT == weight:
        ret.append(reg_plugin)

    return ret


class WinRegistryParser(interface.BasePluginsParser):
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

  def _ParseRegistryFile(
      self, parser_mediator, winreg_file, registry_file_type):
    """Parses a Windows Registry file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      winreg_file: A Windows Registry file (instance of dfwinreg.WinRegFile).
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.
    """
    # TODO: move to separate function.
    plugins = {}
    number_of_plugins = 0
    for weight in self._plugins.GetWeights():
      plugins_list = self._plugins.GetWeightPlugins(weight, registry_file_type)
      plugins[weight] = []
      for plugin_class in plugins_list:
        plugin_object = plugin_class()
        plugins[weight].append(plugin_object)
        number_of_plugins += 1

    logging.debug(
        u'Number of plugins for this Windows Registry file: {0:d}.'.format(
            number_of_plugins))

    # Recurse through keys in the file and apply the plugins in the order:
    # 1. file type specific key-based plugins.
    # 2. generic key-based plugins.
    # 3. file type specific value-based plugins.
    # 4. generic value-based plugins.

    for key in winreg_file.RecurseKeys():
      for weight in iter(plugins.keys()):
        # TODO: determine if the plugin matches the key and continue
        # to the next key.
        for plugin in plugins[weight]:
          if parser_mediator.abort:
            break

          plugin.UpdateChainAndProcess(
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
    file_entry = parser_mediator.GetFileEntry()
    try:
      winreg_file = self._win_registry.OpenFileEntry(
          file_entry, codepage=parser_mediator.codepage)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, display_name, exception))

    try:
      registry_file_type = self._win_registry.GetRegistryFileType(winreg_file)
      logging.debug(
          u'Windows Registry file {0:s}: detected as: {1:s}'.format(
              display_name, registry_file_type))

      self._ParseRegistryFile(parser_mediator, winreg_file, registry_file_type)

    finally:
      winreg_file.Close()


manager.ParsersManager.RegisterParser(WinRegistryParser)
