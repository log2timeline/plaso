# -*- coding: utf-8 -*-
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

  def Process(self, unused_parser_mediator, **kwargs):
    """Evaluates if this is the correct plugin and processes data accordingly.

    The purpose of the process function is to evaluate if this particular
    plugin is the correct one for the particular data structure at hand.
    This function accepts one value to use for evaluation, that could be
    a registry key, list of table names for a database or any other criteria
    that can be used to evaluate if the plugin should be run or not.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      kwargs: Depending on the plugin they may require different sets of
              arguments to be able to evaluate whether or not this is
              the correct plugin.

    Raises:
      ValueError: When there are unused keyword arguments.
    """
    if kwargs:
      raise ValueError(u'Unused keyword arguments: {0:s}.'.format(
          kwargs.keys()))

  def UpdateChainAndProcess(self, parser_mediator, **kwargs):
    """Wrapper for Process() to synchronize the parser chain.

    This convenience method updates the parser chain object held by the
    mediator, transfers control to the plugin-specific Process() method,
    and updates the chain again once the processing is complete. It provides a
    simpler parser API in most cases.
    """
    parser_mediator.AppendToParserChain(self)
    self.Process(parser_mediator, **kwargs)
    parser_mediator.PopFromParserChain()


class BasePluginCache(object):
  """A generic cache object for plugins.

  This cache object can be used to store various information that needs
  to be cached to speed up code execution.
  """

  def GetResults(self, attribute):
    """Return back a cached attribute if it exists."""
    return getattr(self, attribute, None)
