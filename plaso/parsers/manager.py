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

from plaso.frontend import presets


class ParsersManager(object):
  """Class that implements the parsers manager."""

  _parser_classes = {}

  _parser_filter_string = u''

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

        if parser_class.SupportsPlugins():
          active_list.extend(parser_class.GetPluginNames())

      elif filter_string in preset_categories:
        active_list.extend(
            presets.GetParsersFromCategory(filter_string))

      else:
        active_list.append(filter_string)

    return includes, excludes

  @classmethod
  def GetParserNames(cls, parser_filter_string=None):
    """Retrieves the parser names.

    Args:
      parser_filter_string: Optional parser filter string. The default is None.

    Returns:
      A list of parser names.
    """
    parser_names = []

    for parser_name, _ in cls.GetParsers(
        parser_filter_string=parser_filter_string):
      parser_names.append(parser_name)

    return parser_names

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
  def RegisterParsers(cls, parser_classes):
    """Registers parser classes.

    The parser classes are identified based on their lower case name.

    Args:
      parser_classes: a list of class objects of the parsers.

    Raises:
      KeyError: if parser class is already set for the corresponding name.
    """
    for parser_class in parser_classes:
      cls.RegisterParser(parser_class)

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
