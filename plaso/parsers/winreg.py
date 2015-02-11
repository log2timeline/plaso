#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parser for Windows NT Registry (REGF) files."""

import logging
import os

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
    return plugins_dict.get(plugin_type, []) + plugins_dict.get('any', [])

  def AddPlugin(self, plugin_type, plugin_class):
    """Add a Windows Registry plugin to the plugin list.

    Args:
      plugin_type: String containing the Windows Registry type,
                   e.g. NTUSER, SOFTWARE.
      plugin_class: The plugin class that is being registered.
    """
    # Cannot import the interface here otherwise this will create a cyclic
    # dependency.
    if hasattr(plugin_class, 'REG_VALUES'):
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

  def GetWeightPlugins(self, weight, plugin_type=''):
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

  NAME = 'winreg'
  DESCRIPTION = u'Parser for Windows NT Registry (REGF) files.'

  _plugin_classes = {}

  # List of types Windows Registry types and required keys to identify each of
  # these types.
  REG_TYPES = {
      'NTUSER': ('\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer',),
      'SOFTWARE': ('\\Microsoft\\Windows\\CurrentVersion\\App Paths',),
      'SECURITY': ('\\Policy\\PolAdtEv',),
      'SYSTEM': ('\\Select',),
      'SAM': ('\\SAM\\Domains\\Account\\Users',),
      'UNKNOWN': (),
  }

  def __init__(self):
    """Initializes a parser object."""
    super(WinRegistryParser, self).__init__()
    self._plugins = WinRegistryParser.GetPluginList()

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
    """Extract data from a Windows Registry file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    # TODO: Remove this magic reads when the classifier has been
    # implemented, until then we need to make sure we are dealing with
    # a Windows NT Registry file before proceeding.
    magic = 'regf'

    file_entry = parser_mediator.GetFileEntry()
    file_object = parser_mediator.GetFileObject()
    file_object.seek(0, os.SEEK_SET)
    data = file_object.read(len(magic))
    file_object.close()

    if data != magic:
      raise errors.UnableToParseFile((
          u'[{0:s}] unable to parse file: {1:s} with error: invalid '
          u'signature.').format(self.NAME, file_entry.name))

    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    # Determine type, find all parsers
    try:
      winreg_file = registry.OpenFile(
          file_entry, codepage=parser_mediator.codepage)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, file_entry.name, exception))

    # Detect the Windows Registry file type.
    registry_type = 'UNKNOWN'
    for reg_type in self.REG_TYPES:
      if reg_type == 'UNKNOWN':
        continue

      # Check if all the known keys for a certain Registry file exist.
      known_keys_found = True
      for known_key_path in self.REG_TYPES[reg_type]:
        if not winreg_file.GetKeyByPath(known_key_path):
          known_keys_found = False
          break

      if known_keys_found:
        registry_type = reg_type
        break

    self._registry_type = registry_type
    logging.debug(
        u'Windows Registry file {0:s}: detected as: {1:s}'.format(
            file_entry.name, registry_type))

    registry_cache = cache.WinRegistryCache()
    registry_cache.BuildCache(winreg_file, registry_type)

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
      for weight in plugins.iterkeys():
        # TODO: determine if the plugin matches the key and continue
        # to the next key.
        for plugin in plugins[weight]:
          if parser_mediator.abort:
            break
          plugin.UpdateChainAndProcess(
              parser_mediator, key=key, registry_type=self._registry_type,
              codepage=parser_mediator.codepage)


    winreg_file.Close()


manager.ParsersManager.RegisterParser(WinRegistryParser)
