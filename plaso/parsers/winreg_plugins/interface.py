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

from plaso.lib import plugin


class RegistryPlugin(plugin.BasePlugin):
  """Registry plugin takes a registry key and extracts entries from it.

  The entries that are extracted are in the form of an EventObject that
  describes the content of the registry key in a human readable format.
  """

  NAME = 'winreg'

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

  def __init__(self, hive=None, pre_obj=None, reg_cache=None):
    """Constructor for a registry plugin.

    Args:
      hive: A WinRegistry value that stores the hive object, in case we need
      to get values from other keys in the hive.
      pre_obj: The pre-processing object that contains information gathered
      during preprocessing of data.
      rec_cache: A Windows registry cache object.
    """
    super(RegistryPlugin, self).__init__(pre_obj)
    self._hive = hive
    self._config = pre_obj
    self._reg_cache = reg_cache

  @abc.abstractmethod
  def GetEntries(self):
    """Extract and return EventObjects from the registry key."""

  # We need to squash down the linter complaint, should not be here.
  # TODO: Remove this pylint disable.
  # pylint: disable-msg=arguments-differ
  @abc.abstractmethod
  def Process(self, key):
    """Determine if plugin should process and then process.

    Args:
      key: A WinRegKey object that represents the registry key.
    """
    self._key = key


# We are not implementing GetEntries for a purpose, since we want
# plugins that extend this one to do so.
# pylint: disable-msg=abstract-method
class KeyPlugin(RegistryPlugin):
  """A key-based registry plugin implementation."""

  __abstract = True

  # The path of the registry key this plugin supports.
  REG_KEY = None

  WEIGHT = 1

  def Process(self, key):
    """Process the key based plugin."""
    key_fixed = u''
    try:
      key_fixed = ExpandRegistryPath(
          self.REG_KEY, self._config, self._reg_cache)
    except KeyError as e:
      logging.warning(u'Unable to use plugin %s, error message: %s',
                      self.plugin_name, e)

    if not key_fixed:
      return

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


# We are not implementing GetEntries for a purpose, since we want
# plugins that extend this one to do so.
# pylint: disable-msg=abstract-method
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

  def GetValuePlugins(self, plugin_type):
    """Returns a list of all value plugins for a given type of registry."""
    return GetPlugins(self._value_plugins, plugin_type)

  def GetKeyPlugins(self, plugin_type):
    """Returns a list of all key plugins for a given type of registry."""
    return GetPlugins(self._key_plugins, plugin_type)

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


def GetPlugins(plugin_dict, plugin_type):
  """Return all plugins as a list for a specific plugin type."""
  return plugin_dict.get(plugin_type, []) + plugin_dict.get('any', [])


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

  for plugin_cls in plugin.GetRegisteredPlugins(
      RegistryPlugin).itervalues():
    plugin_type = plugin_cls.REG_TYPE
    plugins.AddPlugin(
        plugin_type, plugin_cls.classes.get(plugin_cls.plugin_name))

  return plugins


def ExpandRegistryPath(key_str, pre_obj=None, reg_cache=None):
  """Expand a registry path based on attributes in pre calculated values.

  A registry key path may contain paths that are attributes, based on
  calculations from either preprocessing or based on each individual
  registry file.

  An attribute is defined as anything within a curly bracket, eg.
  "\\System\\{my_attribute}\\Path\\Keyname". If the attribute my_attribute
  is defined in either the pre processing object or the registry cache
  it's value will be replaced with the attribute name, eg
  "\\System\\MyValue\\Path\\Keyname".

  If the registry path needs to have curly brackets in the path then
  they need to be escaped with another curly bracket, eg
  "\\System\\{my_attribute}\\{{123-AF25-E523}}\\KeyName". In this
  case the {{123-AF25-E523}} will be replaced with "{123-AF25-E523}".

  Args:
    key_str: The registry key string before being expanded.
    pre_obj: The PlasoPreprocess object that contains stored values from
    the image.
    reg_cache: A registry cache object.

  Raises:
    KeyError: If an attribute name is in the key path yet not set in
    either the registry cache nor in the pre processing object a KeyError
    will be raised.

  Returns:
    A registry key path that's expanded based on attribute values.
  """
  key_fixed = u''
  key_dict = {}
  if reg_cache:
    key_dict.update(reg_cache.attributes.items())

  if pre_obj:
    key_dict.update(pre_obj.__dict__.items())

  try:
    key_fixed = key_str.format(**key_dict)
  except KeyError as e:
    raise KeyError(u'Unable to expand string, %s' % e)

  if not key_fixed:
    raise KeyError(u'Unable expand string, no string returned.')

  return key_fixed
