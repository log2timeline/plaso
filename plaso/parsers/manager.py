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
"""The parsers and plugins manager objects."""

import logging

from plaso.frontend import presets
from plaso.lib import putils
from plaso.parsers import interface
from plaso.parsers import plugins


class ParsersManager(object):
  """Class that implements the parsers manager."""

  _parser_filter_string = u''

  @classmethod
  def _GetParsersFromPlugins(cls, filter_strings, exclude_strings=None):
    """Return a list of parsers from plugin names.

    To be able to just select particular plugins to be used we need a method
    that can take a plugin name and locate the appropriate parser for that
    plugin. That is the purpose of this method, it takes a list of names,
    checks to see if it is a plugin name and then returns the names of the
    parsers responsible for that plugin.

    Args:
      filter_strings: A list of plugin names.
      exclude_strings: A list of plugins or parsers that should not be
                       included in the results.

    Returns:
      A list of parsers that make use of the supplied plugins.
    """
    parser_list = []

    if not filter_strings:
      return parser_list

    if exclude_strings and type(exclude_strings) not in (tuple, list):
      return parser_list

    for parser_include in filter_strings:
      plugin_cls = plugins.BasePlugin.classes.get(parser_include)

      if not plugin_cls:
        continue

      # Skip if the plugin is in the exclude list.
      if exclude_strings and parser_include in exclude_strings:
        continue
      parent = getattr(plugin_cls, 'parent_class')
      parent_name = getattr(parent, 'NAME', u'')

      if not parent_name:
        logging.warning(u'Class {0:s} does not have a parent.'.format(
            plugin_cls.NAME))
        continue

      # Only include if parser is not in the original filter string and not
      # in the return list.
      if (parent_name and parent_name not in filter_strings and
          parent_name not in parser_list):
        parser_list.append(parent_name)

    return parser_list

  @classmethod
  def _GetParserListsFromString(cls, parser_string):
    """Return a list of parsers to include and exclude from a string.

    Takes a comma separated string and splits it up into two lists,
    of parsers or plugins to include and to exclude from selection.
    If a particular filter is prepended with a minus sign it will
    be included int he exclude section, otherwise in the include.

    Args:
      parser_string: The comma separated string.

    Returns:
      A tuple of two lists, include and exclude.
    """
    include = []
    exclude = []

    preset_categories = presets.categories.keys()

    for filter_string in parser_string.split(','):
      filter_string = filter_string.strip()
      if not filter_string:
        continue
      if filter_string.startswith('-'):
        filter_strings_use = exclude
        filter_string = filter_string[1:]
      else:
        filter_strings_use = include

      filter_string_lower = filter_string.lower()
      if filter_string_lower in preset_categories:
        filter_strings_use.extend(
            presets.GetParsersFromCategory(filter_string_lower))
      else:
        filter_strings_use.append(filter_string_lower)

    return include, exclude

  @classmethod
  def FindAllParsers(cls, pre_obj=None):
    """Find all available parser objects.

    A parser is defined as an object that implements the BaseParser
    class and does not have the __abstract attribute set.

    Each entry in the list can be prepended with a minus sign to signify a
    negative match against a parser, eg: 'winxp,-*lnk*' would select all the
    parsers in the "winxp" preset, EXCEPT parsers that have the substring
    "lnk" somewhere in the parser name.

    Args:
      pre_obj: A preprocess object containing information collected from
               an image (instance of PreprocessObject).

    Returns:
      A dict that contains a list of all detected parsers. The key values in
      the dict will represent the type of the parser, eg 'all' will contain
      all parsers, while other keys will contain a subset of them, e.g.:
      'sqlite' will contain parsers capable of parsing SQLite databases.
    """
    if not pre_obj:
      pre_obj = putils.Options()

    # Process the filter string.
    filter_include, filter_exclude = cls._GetParserListsFromString(
        cls._parser_filter_string)

    # Extend the include using potential plugin names.
    filter_include.extend(
        cls._GetParsersFromPlugins(filter_include, filter_exclude))

    results = {}
    results['all'] = []
    # The pre_obj adds the value of the parser knowing time zone information,
    # and other values that the preprocssing object collects.
    # TODO: remove pre_obj pass specific values e.g.
    # parser_expression. Also see if some of these values can be passed after
    # initialization.
    # pylint: disable=protected-access
    for parser_obj in putils._FindClasses(
        interface.BaseParser, pre_obj):
      add = False
      if not (filter_exclude or filter_include):
        add = True
      else:
        parser_name = parser_obj.parser_name.lower()

        if parser_name in filter_include:
          add = True

        # If a parser is specifically excluded it trumps include rules.
        if parser_name in filter_exclude:
          add = False

      if add:
        results['all'].append(parser_obj)
        # TODO: Find a way to reintroduce PARSER_TYPE using other mechanism to
        # group parsers together.

    return results

  @classmethod
  def GetRegisteredPlugins(cls, parent_class=plugins.BasePlugin, pre_obj=None):
    """Build a list of all available plugins and return them.

    This method uses the class registration library to find all classes that
    have implemented the plugin class.

    This should mostly be used by parsers or other assistant methods that
    know the parent class of the plugin (something like the base class for
    all Windows registry plugins, etc).

    Args:
      parent_class: The top level class of the specific plugin to query.
      pre_obj: The preprocessing object or the knowledge base.

    Returns:
      A dict with keys being the plugin names and values the plugin class.

    Raises:
      ValueError: If two plugins have the same name.
    """
    if cls._parser_filter_string:
      parser_include, parser_exclude = cls._GetParserListsFromString(
          cls._parser_filter_string)

    results = {}
    all_plugins = {}

    for plugin_name, plugin_cls in parent_class.classes.iteritems():
      # Go through the entire chain of parents to see if we have a match.
      # We need to do that in case some plugins inherit from other plugins
      # to add minor enhancements and need to be included in the list of
      # plugins. This is common behavior with registry plugins for instance.
      plugin_parent = plugin_cls
      plugin_match = False
      while plugin_parent != object:
        parent_name = getattr(plugin_parent, 'parent_class_name', 'NOTHERE')

        if parent_name == parent_class.NAME:
          plugin_match = True
          break
        plugin_parent = getattr(plugin_parent, 'parent_class', object)

      if not plugin_match:
        continue

      if plugin_name in all_plugins:
        raise ValueError(
            u'The plugin "{0:s}" appears twice in the plugin list.'.format(
                plugin_name))

      if not cls._parser_filter_string:
        all_plugins[plugin_name] = plugin_cls(pre_obj=pre_obj)
      else:
        if plugin_name in parser_include and plugin_name not in parser_exclude:
          results[plugin_name] = plugin_cls(pre_obj=pre_obj)
        if plugin_name not in parser_exclude:
          all_plugins[plugin_name] = plugin_cls(pre_obj=pre_obj)

    if cls._parser_filter_string and results:
      return results

    return all_plugins

  @classmethod
  def SetParserFilterString(cls, parser_filter_string):
    """Sets the parser filter string.

    The parser_filter_string is a simple comma separated value string that
    denotes a list of parser names to include and/or exclude. Each entry
    can have the value of:
      + Exact match of a list of parsers, or a preset (see
        plaso/frontend/presets.py for a full list of available presets).
      + A name of a single parser (case insensitive), eg. msiecfparser.
      + A glob name for a single parser, eg: '*msie*' (case insensitive).

    Args:
      parser_filter_string: The parser filter string.
    """
    cls._parser_filter_string = parser_filter_string
