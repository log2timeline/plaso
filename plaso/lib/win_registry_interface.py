#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains basic interface for registry handling within Plaso.

This library serves a basis for defining interfaces for registry keys, values
and other items that may need defining.

This is provided as a separate file to make it easier to inherit in other
projects that may want to use the registry plugin system in Plaso.
"""
import abc
import logging
import struct

from plaso.lib import errors
from plaso.lib import registry
from plaso.lib import utils


class RegistryPlugin(object):
  """Registry plugin takes a registry key and extracts entries from it.

  The entries that are extracted are in the form of an EventObject that
  describes the content of the registry key in a human readable format.
  """

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # Indicate the type of hive this plugin belongs to (eg. NTUSER, SOFTWARE).
  REG_TYPE = 'any'

  # The URLS should contain a list of URL's with additional information about
  # this key or value.
  URLS = []
  # WEIGHT is a simple integer value representing the priority of this plugin.
  # The weight can be used by some parser implementation to prioritize the
  # order in which plugins are run against registry keys.
  # By default no registry plugin should overwrite this value, it should only
  # be defined in interfaces extending the base class, providing higher level of
  # prioritization to registry plugins.
  WEIGHT = 3

  def __init__(self, hive, pre_obj):
    """Constructor for a registry plugin.

    Args:
      hive: A WinRegistry value that stores the hive object, in case we need
      to get values from other keys in the hive.
      pre_obj: The pre-processing object that contains information gathered
      during preprocessing of data.
    """
    self._hive = hive
    self._config = pre_obj

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.__class__.__name__

  @abc.abstractmethod
  def GetEntries(self):
    """Extract and return EventObjects from the registry key."""

  def __iter__(self):
    """Return all EventObjects from the object."""
    if hasattr(self, '_key'):
      for entry in self.GetEntries():
        yield entry
    yield None

  @abc.abstractmethod
  def Process(self, key):
    """Determine if plugin should process and then process.

    Args:
      key: A WinRegKey object that represents the registry key.
    """
    self._key = key


class KeyPlugin(RegistryPlugin):
  """A key-based registry plugin implementation."""

  __abstract = True

  # The path of the registry key this plugin supports.
  REG_KEY = None

  WEIGHT = 1

  def Process(self, key):
    """Process the key based plugin."""
    try:
      key_fixed = utils.PathReplacer(self._config, self.REG_KEY).GetPath()
    except errors.PathNotFound as e:
      logging.warning(u'Unable to use plugin %s, error message: %s',
                      self.plugin_name, e)
      return None

    # Special case of Wow6432 registry redirection.
    # URL:  http://msdn.microsoft.com/en-us/library/windows/desktop/\
    # ms724072%28v=vs.85%29.aspx
    if key_fixed.startswith('\\Software'):
      _, first, second = key_fixed.partition('\\Software')
      key_redirect = u'{}\\Wow6432Node{}'.format(first, second)

      if key_redirect == key.path:
        self._key = key
        return self.GetEntries()

    if key.path != key_fixed:
      return None

    self._key = key
    return self.GetEntries()


class ValuePlugin(RegistryPlugin):
  """A value-based registry plugin implementation."""

  __abstract = True

  # REG_VALUES should be defined as a frozenset.
  REG_VALUES = frozenset()

  WEIGHT = 2

  def Process(self, key):
    """Process the value based plugin."""
    values = frozenset([val.name for val in key.GetValues()])
    if self.REG_VALUES.issubset(values):
      self._key = key
      return self.GetEntries()


class PluginList(object):
  """A simple class that stores information about registry plugins."""

  def __init__(self):
    """Default constructor for the plugin list."""
    self._key_plugins = {}
    self._value_plugins = {}

  def AddPlugin(self, plugin_type, plugin_class):
    """Add a registry plugin to the container.

    Args:
      plugin_type: A string denoting the registry type, eg. NTUSER, SOFTWARE.
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
    """Return a list of a all classes that implement value centric plugins."""
    ret = []
    _ = map(ret.extend, self._value_plugins.values())
    return ret

  def _GetPlugins(self, plugin_dict, plugin_type):
    """Return all plugins as a list for a specific plugin type."""
    return plugin_dict.get(plugin_type, []) + plugin_dict.get('any', [])

  def GetValuePlugins(self, plugin_type):
    """Returns a list of all value plugins for a given type of registry."""
    return self._GetPlugins(self._value_plugins, plugin_type)

  def GetKeyPlugins(self, plugin_type):
    """Returns a list of all key plugins for a given type of registry."""
    return self._GetPlugins(self._key_plugins, plugin_type)

  def GetWeightPlugins(self, weight, plugin_type=''):
    """Return a list of all plugins for a given weight or priority.

    Each plugin defines a weight or a priority that defines in which order
    it should be processed in the case of a parser that applies priority.

    This method returns all plugins, whether they are key or value based
    that use a defined weight or priority and are defined to parse keys
    or values found in a certain registry type.

    Args:
      weight: An integer representing the weight or priority (usually a
      number from 1 to 3).
      plugin_type: A string that defines the registry type, eg. NTUSER,
      SOFTWARE, etc.

    Returns:
      A list that contains all the plugins that fit the defined criteria.
    """
    ret = []
    for plugin in self.GetKeyPlugins(plugin_type):
      if plugin.WEIGHT == weight:
        ret.append(plugin)

    for plugin in self.GetValuePlugins(plugin_type):
      if plugin.WEIGHT == weight:
        ret.append(plugin)

    return ret

  def GetWeights(self):
    """Return a set of all weights/priority of the loaded plugins."""
    return set(plugin.WEIGHT for plugin in self.GetAllValuePlugins()).union(
        plugin.WEIGHT for plugin in self.GetAllKeyPlugins())

  def GetTypes(self):
    """Return a set of all plugins supported."""
    return set(self._key_plugins).union(self._value_plugins)


def GetRegistryPlugins():
  """Build a list of all available plugins capable of parsing the registry.

  This method uses the class registration library to find all classes that have
  implemented the RegistryPlugin class and compiles two dictionaries, one
  containing a list of all plugins that support key-centric plugins and then
  another one that contains plugins that are value-centric.

  Returns:
    Two dictionaries, key_centric and value_centric used for plugin detection.
  """
  plugins = PluginList()

  for plugin_cls in RegistryPlugin.classes.values():
    plugin_type = plugin_cls.REG_TYPE
    plugins.AddPlugin(plugin_type, plugin_cls)

  return plugins

