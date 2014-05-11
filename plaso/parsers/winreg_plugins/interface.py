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

  def __init__(self, pre_obj=None, reg_cache=None):
    """Initializes Windows Registry plugin object.

    Args:
      pre_obj: Optional preprocessing object that contains information gathered
               during preprocessing of data. The default is None.
      reg_cache: Optional Windows Registry objects cache (instance of
                 WinRegistryCache). The default is None.
    """
    super(RegistryPlugin, self).__init__(pre_obj)
    self._config = pre_obj

    # TODO: Clean this up, this value is stored but not used.
    self._reg_cache = reg_cache

  @abc.abstractmethod
  def GetEntries(self, key=None, **kwargs):
    """Extracts event objects from the Windows Registry key."""

  def Process(self, key=None, **kwargs):
    """Processes the Windows Registry key or value if the plugin applies.

    Args:
      key: A Windows Registry key (instance of WinRegKey).

    Raises:
      ValueError: If the key value is not set.
    """
    if key is None:
      raise ValueError(u'Key is not set.')

    super(RegistryPlugin, self).Process(**kwargs)


class KeyPlugin(RegistryPlugin):
  """Class that defines the Windows Registry key-based plugin interface."""

  __abstract = True

  # A list of all the Windows Registry key paths this plugins supports.
  # Each of these key paths can contain a path that needs to be expanded,
  # such as {current_control_set}, etc.
  REG_KEYS = []

  WEIGHT = 1

  def __init__(self, pre_obj=None, reg_cache=None):
    """Initializes key-based Windows Registry plugin object.

    Args:
      pre_obj: Optional preprocessing object that contains information gathered
               during preprocessing of data. The default is None.
      reg_cache: Optional Windows Registry objects cache (instance of
                 WinRegistryCache). The default is None.
    """
    super(KeyPlugin, self).__init__(pre_obj=pre_obj, reg_cache=reg_cache)
    self._path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        pre_obj, reg_cache)

    # Build a list of expanded keys this plugin supports.
    self.expanded_keys = []
    for registry_key in self.REG_KEYS:
      key_fixed = u''
      try:
        key_fixed = self._path_expander.ExpandPath(registry_key)
        self.expanded_keys.append(key_fixed)
      except KeyError as exception:
        logging.debug((
            u'Unable to use registry key {0:s} for plugin {1:s}, error '
            u'message: {1:s}').format(
                registry_key, self.plugin_name, exception))
        continue

      if not key_fixed:
        continue
      # Special case of Wow6432 Windows Registry redirection.
      # URL:  http://msdn.microsoft.com/en-us/library/windows/desktop/\
      # ms724072%28v=vs.85%29.aspx
      if key_fixed.startswith('\\Software'):
        _, first, second = key_fixed.partition('\\Software')
        self.expanded_keys.append(u'{0:s}\\Wow6432Node{1:s}'.format(
            first, second))
      if self.REG_TYPE == 'SOFTWARE' or self.REG_TYPE == 'any':
        self.expanded_keys.append(u'\\Wow6432Node{:s}'.format(key_fixed))

  @abc.abstractmethod
  def GetEntries(self, key=None, **kwargs):
    """Extracts event objects from the Windows Registry key."""

  def Process(self, key=None, **kwargs):
    """Process a Windows Registry key."""
    if not key:
      return

    super(KeyPlugin, self).Process(key=key, **kwargs)

    if key.path in self.expanded_keys:
      return self.GetEntries(key=key)


class ValuePlugin(RegistryPlugin):
  """Class that defines the Windows Registry value-based plugin interface."""

  __abstract = True

  # REG_VALUES should be defined as a frozenset.
  REG_VALUES = frozenset()

  WEIGHT = 2

  @abc.abstractmethod
  def GetEntries(self, key=None, **kwargs):
    """Extracts event objects from the Windows Registry key."""

  def Process(self, key=None, **kwargs):
    """Processes the Windows Registry value."""
    super(ValuePlugin, self).Process(key=key, **kwargs)

    values = frozenset([val.name for val in key.GetValues()])
    if self.REG_VALUES.issubset(values):
      return self.GetEntries(key=key)


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
    if issubclass(plugin_class, KeyPlugin):
      self._key_plugins.setdefault(plugin_type, []).append(plugin_class)

    if issubclass(plugin_class, ValuePlugin):
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


def GetRegistryPlugins(filter_list=None):
  """Build a list of all available Windows Registry plugins.

     This function uses the class registration library to find all classes that
     have implemented the RegistryPlugin class.

  Args:
    filter_list: An optional filter criteria to limit the plugins loaded.

  Returns:
    A plugins list (instance of PluginList).
  """
  plugins_list = PluginList()

  for plugin_cls in plugin.GetRegisteredPlugins(
      RegistryPlugin, parser_filter_string=filter_list).itervalues():
    plugin_type = plugin_cls.REG_TYPE
    plugins_list.AddPlugin(
        plugin_type, plugin_cls.classes.get(plugin_cls.plugin_name))

  return plugins_list
