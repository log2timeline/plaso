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
"""The Windows Registry plugin objects interface."""

import abc
import logging

from plaso.lib import plugin
from plaso.winreg import path_expander as winreg_path_expander


class RegistryPlugin(plugin.BasePlugin):
  """Class that defines the Windows Registry plugin object interface."""

  __abstract = True

  NAME = 'winreg'

  # Indicate the type of hive this plugin belongs to (eg. NTUSER, SOFTWARE).
  REG_TYPE = 'any'

  # The URLS should contain a list of URL's with additional information about
  # this key or value.
  URLS = []

  # WEIGHT is a simple integer value representing the priority of this plugin.
  # The weight can be used by some parser implementation to prioritize the
  # order in which plugins are run against the Windows Registry keys.
  # By default no the Windows Registry plugin should overwrite this value,
  # it should only be defined in interfaces extending the base class, providing
  # higher level of prioritization to Windows Registry plugins.
  WEIGHT = 3

  def __init__(self, hive=None, pre_obj=None, reg_cache=None):
    """Initializes Windows Registry plugin object.

    Args:
      hive: Optional Windows Registry hive (instance of WinRegistry).
            The default is None.
      pre_obj: Optional pre-processing object that contains information gathered
               during preprocessing of data. The default is None.
      reg_cache: Optional Windows Registry objects cache (instance of
                 WinRegistryCache). The default is None.
    """
    super(RegistryPlugin, self).__init__(pre_obj)
    self._config = pre_obj
    self._hive = hive
    # TODO: Clean this up, this value is stored but not used. 
    self._reg_cache = reg_cache

  @abc.abstractmethod
  def GetEntries(self):
    """Extracts event objects from the Windows Registry key."""

  # TODO: Fix this, either make RegistryPlugin a separate interface
  # or use kwargs to create a coherent plugin interface.
  # pylint: disable-msg=arguments-differ
  def Process(self, key):
    """Determine if plugin should process and then process.

    Args:
      key: A Windows Registry key (instance of WinRegKey).
    """
    self._key = key


class KeyPlugin(RegistryPlugin):
  """Class that defines the Windows Registry key-based plugin interface."""

  __abstract = True

  # The path of the Windows Registry key this plugin supports.
  REG_KEY = None

  WEIGHT = 1

  def __init__(self, hive=None, pre_obj=None, reg_cache=None):
    """Initializes key-based Windows Registry plugin object.

    Args:
      hive: Optional Windows Registry hive (instance of WinRegistry).
            The default is None.
      pre_obj: Optional pre-processing object that contains information gathered
               during preprocessing of data. The default is None.
      reg_cache: Optional Windows Registry objects cache (instance of
                 WinRegistryCache). The default is None.
    """
    super(KeyPlugin, self).__init__(
        hive=hive, pre_obj=pre_obj, reg_cache=reg_cache)
    self._path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        pre_obj, reg_cache)

  @abc.abstractmethod
  def GetEntries(self):
    """Extracts event objects from the Windows Registry key."""

  def Process(self, key):
    """Process the key based plugin."""
    key_fixed = u''
    try:
      key_fixed = self._path_expander.ExpandPath(self.REG_KEY)
    except KeyError as e:
      logging.warning(
          u'Unable to use plugin {0:s}, error message: {1:s}'.format(
              self.plugin_name, e))

    if not key_fixed:
      return

    # Special case of Wow6432 Windows Registry redirection.
    # URL:  http://msdn.microsoft.com/en-us/library/windows/desktop/\
    # ms724072%28v=vs.85%29.aspx
    if key_fixed.startswith('\\Software'):
      _, first, second = key_fixed.partition('\\Software')
      key_redirect = u'{0:s}\\Wow6432Node{1:s}'.format(first, second)

      if key_redirect == key.path:
        self._key = key
        return self.GetEntries()

    if key.path != key_fixed:
      return None

    self._key = key
    return self.GetEntries()


class ValuePlugin(RegistryPlugin):
  """Class that defines the Windows Registry value-based plugin interface."""

  __abstract = True

  # REG_VALUES should be defined as a frozenset.
  REG_VALUES = frozenset()

  WEIGHT = 2

  @abc.abstractmethod
  def GetEntries(self):
    """Extracts event objects from the Windows Registry key."""

  def Process(self, key):
    """Process the value based plugin."""
    values = frozenset([val.name for val in key.GetValues()])
    if self.REG_VALUES.issubset(values):
      self._key = key
      return self.GetEntries()


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
    """Add a Windows Registry plugin to the container.

    Args:
      plugin_type: String containing the Windows Registry type,
                   e.g. NTUSER, SOFTWARE.
      plugin_class: The plugin class that is being registered.
    """
    if issubclass(plugin_class, KeyPlugin):
      self._key_plugins.setdefault(plugin_type, []).append(plugin_class)

    if issubclass(plugin_class, ValuePlugin):
      self._value_plugins.setdefault(plugin_type, []).append(plugin_class)

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


def GetRegistryPlugins():
  """Build a list of all available Windows Registry plugins.

     This function uses the class registration library to find all classes that
     have implemented the RegistryPlugin class.

  Returns:
    A plugins list (instance of PluginList).
  """
  plugins_list = PluginList()

  for plugin_cls in plugin.GetRegisteredPlugins(RegistryPlugin).itervalues():
    plugin_type = plugin_cls.REG_TYPE
    plugins_list.AddPlugin(
        plugin_type, plugin_cls.classes.get(plugin_cls.plugin_name))

  return plugins_list
