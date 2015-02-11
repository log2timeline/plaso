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
"""This file contains a class to provide a parsing framework to plaso.

This class contains a base framework class for parsing fileobjects, and
also some implementations that extend it to provide a more comprehensive
parser.
"""

import abc

from plaso.parsers import manager


class BaseParser(object):
  """Class that implements the parser object interface."""

  NAME = 'base_parser'
  DESCRIPTION = u''

  @abc.abstractmethod
  def Parse(self, parser_mediator, **kwargs):
    """Parsers the file entry and extracts event objects.

    This is the main function of the class, the one that actually
    goes through the log file and parses each line of it to
    produce a parsed line and a timestamp.

    It also tries to verify the file structure and see if the class is capable
    of parsing the file passed to the module. It will do so with series of tests
    that should determine if the file is of the correct structure.

    If the class is not capable of parsing the file passed to it an exception
    should be raised, an exception of the type UnableToParseFile that indicates
    the reason why the class does not parse it.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Raises:
      NotImplementedError when not implemented.
    """
    raise NotImplementedError

  def UpdateChainAndParse(self, parser_mediator, **kwargs):
    """Wrapper for Parse() to synchronize the parser chain.

    This convenience method updates the parser chain object held by the
    mediator, transfers control to the parser-specific Parse() method,
    and updates the chain again once the parsing is complete. It provides a
    simpler parser API in most cases.
    """
    parser_mediator.AppendToParserChain(self)
    self.Parse(parser_mediator, **kwargs)
    parser_mediator.PopFromParserChain()

  @classmethod
  def SupportsPlugins(cls):
    """Determines if a parser supports plugins.

    Returns:
      A boolean value indicating whether the parser supports plugins.
    """
    return False


class BasePluginsParser(BaseParser):
  """Class that implements the parser with plugins object interface."""

  NAME = 'base_plugin_parser'
  DESCRIPTION = u''

  # Every child class should define its own _plugin_classes dict.
  # We don't define it here to make sure the plugins of different
  # classes don't end up in the same dict.
  # _plugin_classes = {}
  _plugin_classes = None

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters a plugin class.

    The plugin classes are identified based on their lower case name.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is not set for the corresponding name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name not in cls._plugin_classes:
      raise KeyError(
          u'Plugin class not set for name: {0:s}.'.format(
              plugin_class.NAME))

    del cls._plugin_classes[plugin_name]

  @classmethod
  def GetPluginNames(cls, parser_filter_string=None):
    """Retrieves the plugin names.

    Args:
      parser_filter_string: Optional parser filter string. The default is None.

    Returns:
      A list of plugin names.
    """
    plugin_names = []

    for plugin_name, _ in cls.GetPlugins(
        parser_filter_string=parser_filter_string):
      plugin_names.append(plugin_name)

    return plugin_names

  @classmethod
  def GetPluginObjects(cls, parser_filter_string=None):
    """Retrieves the plugin objects.

    Args:
      parser_filter_string: Optional parser filter string. The default is None.

    Returns:
      A list of plugin objects (instances of BasePlugin).
    """
    plugin_objects = []

    for _, plugin_class in cls.GetPlugins(
        parser_filter_string=parser_filter_string):
      plugin_object = plugin_class()
      plugin_objects.append(plugin_object)

    return plugin_objects

  @classmethod
  def GetPlugins(cls, parser_filter_string=None):
    """Retrieves the registered plugins.

    Args:
      parser_filter_string: Optional parser filter string. The default is None.

    Yields:
      A tuple that contains the uniquely identifying name of the plugin
      and the plugin class (subclass of BasePlugin).
    """
    if parser_filter_string:
      includes, excludes = manager.ParsersManager.GetFilterListsFromString(
          parser_filter_string)
    else:
      includes = None
      excludes = None

    for plugin_name, plugin_class in cls._plugin_classes.iteritems():
      if excludes and plugin_name in excludes:
        continue

      if includes and plugin_name not in includes:
        continue

      yield plugin_name, plugin_class

  @abc.abstractmethod
  def Parse(self, parser_mediator, **kwargs):
    """Parsers the file entry and extracts event objects.

    This is the main function of the class, the one that actually
    goes through the log file and parses each line of it to
    produce a parsed line and a timestamp.

    It also tries to verify the file structure and see if the class is capable
    of parsing the file passed to the module. It will do so with series of tests
    that should determine if the file is of the correct structure.

    If the class is not capable of parsing the file passed to it an exception
    should be raised, an exception of the type UnableToParseFile that indicates
    the reason why the class does not parse it.

    Args:
      parser_mediator: A parser context object (instance of ParserMediator).

    Raises:
      NotImplementedError when not implemented.
    """
    raise NotImplementedError

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers a plugin class.

    The plugin classes are identified based on their lower case name.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name in cls._plugin_classes:
      raise KeyError((
          u'Plugin class already set for name: {0:s}.').format(
              plugin_class.NAME))

    cls._plugin_classes[plugin_name] = plugin_class

  @classmethod
  def RegisterPlugins(cls, plugin_classes):
    """Registers plugin classes.

    Args:
      plugin_classes: a list of class objects of the plugins.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    for plugin_class in plugin_classes:
      cls.RegisterPlugin(plugin_class)

  @classmethod
  def SupportsPlugins(cls):
    """Determines if a parser supports plugins.

    Returns:
      A boolean value indicating whether the parser supports plugins.
    """
    return True
