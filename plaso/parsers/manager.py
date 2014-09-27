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
from plaso.parsers import plugins


class ParsersManager(object):
  """Class that implements the parsers manager."""

  _parser_classes = {}

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
  def DeregisterParser(cls, parser_class):
    """Deregisters a parser class.

    The parser classes are identified based on their lower case name.

    Args:
      parser_class: the class object of the parser.

    Raises:
      KeyError: if parser class is not set for the corresponding name.
    """
    parser_name = parser_class.NAME.lower()
    if parser_name not in cls._parser_classes:
      raise KeyError(
          u'Parser class not set for name: {0:s}.'.format(
              parser_class.NAME))

    del cls._parser_classes[parser_name]

  @classmethod
  def GetFilterListsFromString(cls, parser_filter_string):
    """Determines an include and exclude list of parser and plugin names.

    Takes a comma separated string and splits it up into two lists,
    of parsers or plugins to include and to exclude from selection.
    If a particular filter is prepended with a minus sign it will
    be included in the exclude section, otherwise in the include.

    Args:
      parser_filter_string: The parser filter string.

    Returns:
      A tuple of two lists, include and exclude.
    """
    includes = []
    excludes = []

    preset_categories = presets.categories.keys()

    for filter_string in parser_filter_string.split(','):
      filter_string = filter_string.strip()
      if not filter_string:
        continue

      if filter_string.startswith('-'):
        active_list = excludes
        filter_string = filter_string[1:]
      else:
        active_list = includes

      filter_string = filter_string.lower()
      if filter_string in cls._parser_classes:
        parser_class = cls._parser_classes[filter_string]
        active_list.append(filter_string)
        active_list.extend(parser_class.GetPluginNames())

      elif filter_string in preset_categories:
        active_list.extend(
            presets.GetParsersFromCategory(filter_string))

      else:
        active_list.append(filter_string)

    return includes, excludes

  @classmethod
  def GetParserObjects(cls, parser_filter_string=None):
    """Retrieves the parser objects.

    Args:
      parser_filter_string: Optional parser filter string. The default is None.

    Returns:
      A list of parser objects (instances of BaseParser).
    """
    parser_objects = []

    for _, parser_class in cls.GetParsers(
        parser_filter_string=parser_filter_string):
      parser_object = parser_class()
      parser_objects.append(parser_object)

    return parser_objects

  @classmethod
  def GetParsers(cls, parser_filter_string=None):
    """Retrieves the registered parsers.

    Args:
      parser_filter_string: Optional parser filter string. The default is None.

    Yields:
      A tuple that contains the uniquely identifying name of the parser
      and the parser class (subclass of BaseParser).
    """
    if parser_filter_string:
      includes, excludes = cls.GetFilterListsFromString(parser_filter_string)
    else:
      includes = None
      excludes = None

    for parser_name, parser_class in cls._parser_classes.iteritems():
      if excludes and parser_name in excludes:
        continue

      if includes and parser_name not in includes:
        continue

      yield parser_name, parser_class

  # TODO: remove once no longer used in pshell.
  @classmethod
  def FindAllParsers(cls):
    """Find all available parser objects.

    A parser is defined as an object that implements the BaseParser class.

    Each entry in the list can be prepended with a minus sign to signify a
    negative match against a parser, eg: 'winxp,-*lnk*' would select all the
    parsers in the "winxp" preset, EXCEPT parsers that have the substring
    "lnk" somewhere in the parser name.

    Returns:
      A dict that contains a list of all detected parsers. The key values in
      the dict will represent the type of the parser, eg 'all' will contain
      all parsers, while other keys will contain a subset of them, e.g.:
      'sqlite' will contain parsers capable of parsing SQLite databases.
    """
    # Process the filter string.
    filter_include, filter_exclude = cls.GetFilterListsFromString(
        cls._parser_filter_string)

    # Extend the include using potential plugin names.
    # filter_include.extend(
    #     cls._GetParsersFromPlugins(filter_include, filter_exclude))

    results = {}
    results['all'] = []

    for parser_name, parser_class in cls._parser_classes.iteritems():
      if not (filter_exclude or filter_include):
        add = True

      elif parser_name in filter_include:
        add = True

      # If a parser is specifically excluded it trumps include rules.
      # TODO: what if a parser is defined in both the include and
      # exclude filters?
      elif parser_name in filter_exclude:
        add = False

      else:
        add = False

      if add:
        results['all'].append(parser_class)
        # TODO: Find a way to reintroduce PARSER_TYPE using other mechanism to
        # group parsers together.

    return results

  @classmethod
  def GetWindowsRegistryPlugins(cls):
    """Build a list of all available Windows Registry plugins.

    Returns:
      A plugins list (instance of PluginList).
    """
    parser_class = cls._parser_classes.get('winreg', None)
    if not parser_class:
      return

    return parser_class.GetPluginList()

  @classmethod
  def RegisterParser(cls, parser_class):
    """Registers a parser class.

    The parser classes are identified based on their lower case name.

    Args:
      parser_class: the class object of the parser.

    Raises:
      KeyError: if parser class is already set for the corresponding name.
    """
    parser_name = parser_class.NAME.lower()
    if parser_name in cls._parser_classes:
      raise KeyError((
          u'Parser class already set for name: {0:s}.').format(
              parser_class.NAME))

    cls._parser_classes[parser_name] = parser_class

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
