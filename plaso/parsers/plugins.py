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
"""This file contains basic interface for plugins within Plaso.

This library serves a basis for all plugins in Plaso, whether that are
Windows registry plugins, SQLite plugins or any other parsing plugins.

This is provided as a separate file to make it easier to inherit in other
projects that may want to use the Plaso plugin system.
"""


class BasePlugin(object):
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

  # The name of the plugin. This is the name that is used in the registration
  # and used for parser/plugin selection, so this needs to be concise and unique
  # for all plugins/parsers, eg: 'Chrome', 'Safari', 'UserAssist', etc.
  NAME = 'base_plugin'

  DESCRIPTION = u''

  # The URLS should contain a list of URLs with additional information about
  # the plugin, for instance some additional reading material. That can be
  # a description of the data structure, or how to read the data that comes
  # out of the parser, etc. So in essence this is a field to define pointers
  # to additional resources to assist the practitioner reading the output of
  # the plugin.
  URLS = []

  # TODO: remove.
  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.NAME

  def _BuildParserChain(self, parser_chain=None):
    """Return the parser chain with the addition of the current parser.

    Args:
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.

    Returns:
      The parser chain, with the addition of the current parser.
    """
    if not parser_chain:
      return self.NAME

    return u'/'.join([parser_chain, self.NAME])

  def Process(self, unused_parser_context, unused_parser_chain=None, **kwargs):
    """Evaluates if this is the correct plugin and processes data accordingly.

    The purpose of the process function is to evaluate if this particular
    plugin is the correct one for the particular data structure at hand.
    This function accepts one value to use for evaluation, that could be
    a registry key, list of table names for a database or any other criteria
    that can be used to evaluate if the plugin should be run or not.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      kwargs: Depending on the plugin they may require different sets of
              arguments to be able to evaluate whether or not this is
              the correct plugin.

    Raises:
      ValueError: When there are unused keyword arguments.
    """
    if kwargs:
      raise ValueError(u'Unused keyword arguments: {0:s}.'.format(
          kwargs.keys()))


class BasePluginCache(object):
  """A generic cache object for plugins.

  This cache object can be used to store various information that needs
  to be cached to speed up code execution.
  """

  def GetResults(self, attribute):
    """Return back a cached attribute if it exists."""
    return getattr(self, attribute, None)
