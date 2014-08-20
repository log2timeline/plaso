#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""The Windows Registry plugins list object."""

from plaso.parsers.winreg_plugins import interface


# TODO: add tests for this class.

class PluginList(object):
  """A simple class that stores information about Windows Registry plugins."""

  def __init__(self):
    """Initializes the plugin list object."""
    super(PluginList, self).__init__()
    self._key_plugins = {}
    self._value_plugins = {}

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
    if issubclass(plugin_class, interface.KeyPlugin):
      self._key_plugins.setdefault(plugin_type, []).append(plugin_class)

    if issubclass(plugin_class, interface.ValuePlugin):
      self._value_plugins.setdefault(plugin_type, []).append(plugin_class)

  def __iter__(self):
    """Return an iterator of all Windows Registry plugins."""
    ret = []
    _ = map(ret.extend, self._key_plugins.values())
    _ = map(ret.extend, self._value_plugins.values())
    for item in ret:
      yield item

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

  def GetWeights(self):
    """Return a set of all weights/priority of the loaded plugins."""
    return set(plugin.WEIGHT for plugin in self.GetAllValuePlugins()).union(
        plugin.WEIGHT for plugin in self.GetAllKeyPlugins())

  def GetTypes(self):
    """Return a set of all plugins supported."""
    return set(self._key_plugins).union(self._value_plugins)
