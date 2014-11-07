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
"""The preprocess plugins manager."""

import logging

from plaso.lib import errors


class PreprocessPluginsManager(object):
  """Class that implements the preprocess plugins manager."""

  _plugin_classes = {}

  @classmethod
  def _GetPluginsByWeight(cls, platform, weight):
    """Returns all plugins for a specific platform of a certain weight.

    Args:
      platform: A string containing the supported operating system
                of the plugin.
      weight: An integer containing the weight of the plugin.

    Yields:
      A preprocess plugin objects that matches the platform and weight.
    """
    for plugin_class in cls._plugin_classes.itervalues():
      plugin_supported_os = getattr(plugin_class, 'SUPPORTED_OS', [])
      plugin_weight = getattr(plugin_class, 'WEIGHT', 0)
      if platform in plugin_supported_os and weight == plugin_weight:
        yield plugin_class()

  @classmethod
  def _GetWeights(cls, platform):
    """Returns a list of all weights that are used by preprocessing plugins.

    Args:
      platform: A string containing the supported operating system
                of the plugin.

    Returns:
      A list of weights.
    """
    weights = {}
    for plugin_class in cls._plugin_classes.itervalues():
      plugin_supported_os = getattr(plugin_class, 'SUPPORTED_OS', [])
      plugin_weight = getattr(plugin_class, 'WEIGHT', 0)
      if platform in plugin_supported_os:
        weights[plugin_weight] = 1

    return sorted(weights.keys())

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters a plugin class.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is not set for the corresponding name.
    """
    if plugin_class.__name__ not in cls._plugin_classes:
      raise KeyError(
          u'Plugin class not set for name: {0:s}.'.format(
              plugin_class.__name__))

    del cls._plugin_classes[plugin_class.__name__]

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers a plugin class.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    if plugin_class.__name__ in cls._plugin_classes:
      raise KeyError((
          u'Plugin class already set for name: {0:s}.').format(
              plugin_class.__name__))

    cls._plugin_classes[plugin_class.__name__] = plugin_class

  @classmethod
  def RegisterPlugins(cls, plugin_classes):
    """Registers a plugin classes.

    Args:
      plugin_classes: a list of class objects of the plugins.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    for plugin_class in plugin_classes:
      cls.RegisterPlugin(plugin_class)

  @classmethod
  def RunPlugins(cls, platform, searcher, knowledge_base):
    """Runs the plugins for a specific platform.

    Args:
      platform: A string containing the supported operating system
                of the plugin.
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
    """
    for weight in cls._GetWeights(platform):
      for plugin_object in cls._GetPluginsByWeight(platform, weight):
        try:
          plugin_object.Run(searcher, knowledge_base)

        except (IOError, errors.PreProcessFail) as exception:
          logging.warning((
              u'Unable to run preprocessor: {0:s} for attribute: {1:s} '
              u'with error: {2:s}').format(
                  plugin_object.plugin_name, plugin_object.ATTRIBUTE,
                  exception))
