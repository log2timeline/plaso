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
"""This file contains basic interface for plugins within Plaso.

This library serves a basis for all plugins in Plaso, whether that are
Windows registry plugins, SQLite plugins or any other parsing plugins.

This is provided as a separate file to make it easier to inherit in other
projects that may want to use the Plaso plugin system.
"""
import abc

from plaso.lib import registry
from plaso.lib import putils


class Plugin(object):
  """A plugin is a lightweight parser that makes use of a common data structure.

  When a data structure is common amongst several artifacts or files a plugin
  infrastructure can be written to make writing parsers simpler. The goal of a
  plugin is have only a single parser that understands the data structure that
  can call plugins that have specialized knowledge of certain structures.

  An example of this is a SQLite database. A plugin can be written that has
  knowledge of certain database, such as Chrome history, or Skype history, etc.
  This can be done without needing to write a full fledged parser that needs
  to re-implement the data structure knowledge. A single parser can be created
  that calls the plugins to see if it knows that particular database.

  Another example is Windows registry, there a single parser that can parse
  the registry can be made and the job of a single plugin is to parse a
  particular registry key. The parser can then read a registry key and compare
  it to a list of available plugins to see if it can be parsed.
  """

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # The URLS should contain a list of URL's with additional information about
  # the plugin, for instance some additional reading material. That can be
  # a description of the data structure, or how to read the data that comes
  # out of the parser, etc. So in essence this is a field to define pointers
  # to additional resources to assist the practioner reading the output of
  # the plugin.
  URLS = []

  # The name of the plugin. This is the name that is used in the registration
  # and used for parser/plugin selection, so this needs to be concise and unique
  # for all plugins/parsers, eg: 'Chrome', 'Safari', 'UserAssist', etc.
  NAME = 'Plugin'

  def __init__(self, pre_obj):
    """Constructor for a plugin.

    Args:
      pre_obj: The pre-processing object that contains information gathered
               during the pre processing stage. This object contains useful
               information that can be utilized by the plugin.
    """
    self._knowledge_base = pre_obj

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.NAME

  @abc.abstractmethod
  def GetEntries(self):
    """Extract and return EventObjects from the data structure."""

  @abc.abstractmethod
  def Process(self, *kwargs):
    """Evaluate if this is the correct plugin and return a generator.

    The purpose of the process function is to evaluate if this particular
    plugin is the correct one for the particular data structure at hand.
    This function accepts one value to use for evaluation, that could be
    a registry key, list of table names for a database or any other criteria
    that can be used to evaluate if the plugin should be run or not.

    Args:
      kwargs: Depending on the plugin they may require different sets of
      arguments to be able to evaluate whether or not this is the correct
      plugin.

    Returns:
      A generator, self.GetEntries(), if the correct plugin, otherwise None.
    """


def GetRegisteredPlugins(
    parent_class=Plugin, pre_obj=None, parser_filter_string=u''):
  """Build a list of all available plugins and return them.

  This method uses the class registration library to find all classes that have
  implemented the plugin class.

  This should mostly be used by parsers or other assistant methods that know
  the parent class of the plugin (something like the base class for all Windows
  registry plugins, etc).

  Args:
    parent_class: The top level class of the specific plugin to query.
    pre_obj: The pre processing object or the knowledge base.
    parser_filter_string: Optional comma separated list of parsers and plugins
                          to include. The default is an empty string.

  Returns:
    A dict with keys being the plugin names and values the plugin class.

  Raises:
    ValueError: If two plugins have the same name.
  """
  if parser_filter_string:
    parser_include, parser_exclude = putils.GetParserListsFromString(
        parser_filter_string)

  results = {}
  all_plugins = {}

  for plugin_name, plugin_cls in parent_class.classes.iteritems():
    parent_name = getattr(plugin_cls, 'parent_class', 'NOTHERE')

    if parent_name != parent_class.NAME:
      continue

    if plugin_name in all_plugins:
      raise ValueError(
          u'The plugin "{}" appears twice in the plugin list.'.format(
              plugin_name))

    if not parser_filter_string:
      all_plugins[plugin_name] = plugin_cls(pre_obj=pre_obj)
    else:
      if plugin_name in parser_include and plugin_name not in parser_exclude:
        results[plugin_name] = plugin_cls(pre_obj=pre_obj)
      if plugin_name not in parser_exclude:
        all_plugins[plugin_name] = plugin_cls(pre_obj=pre_obj)

  if parser_filter_string and results:
    return results

  return all_plugins
