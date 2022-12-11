# -*- coding: utf-8 -*-
"""This file contains basic interface for plugins within Plaso.

This library serves a basis for all plugins in Plaso, whether that are
Windows Registry plugins, SQLite plugins or any other parsing plugins.

This is provided as a separate file to make it easier to inherit in other
projects that may want to use the Plaso plugin system.
"""


class BasePlugin(object):
  """A plugin is a lightweight parser that makes use of a common data structure.

  When a data structure is common among several artifacts or files a plugin
  infrastructure can be written to make writing parsers simpler. The goal of a
  parser plugin is to have only a single parser that understands the data
  structure that can call plugins that have specialized knowledge of certain
  structures.

  An example of this is a SQLite database. A plugin can be written that has
  knowledge of certain database, such as Chrome history, or Skype history, etc.
  This can be done without needing to write a fully-fledged parser that needs
  to re-implement the data structure knowledge. A single parser can be created
  that calls the plugins to see if it knows that particular database.

  Another example is Windows Registry, there a single parser that can parse
  the Registry can be made and the job of a single plugin is to parse a
  particular Registry key. The parser can then read a Registry key and compare
  it to a list of available plugins to see if it can be parsed.
  """

  # The name of the plugin. This is the name that is used in the registration
  # and used for parser/plugin selection, so this needs to be concise and unique
  # for all plugins/parsers, such as 'Chrome', 'Safari' or 'UserAssist'.
  NAME = 'base_plugin'

  # Data format supported by the parser plugin. This information is used by
  # the parser manager to generate parser and plugin information.
  DATA_FORMAT = ''

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, **kwargs):
    """Extracts events using a parser plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      kwargs (dict[str, object]): Depending on the plugin they may require
          different sets of arguments to be able to evaluate whether or not
          this is the correct plugin.

    Raises:
      ValueError: when there are unused keyword arguments.
    """
    if kwargs:
      raise ValueError('Unused keyword arguments: {0:s}.'.format(
          ', '.join(kwargs.keys())))

  def UpdateChainAndProcess(self, parser_mediator, **kwargs):
    """Extracts events using a parser plugin and synchronizes the parser chain.

    This method updates the parser chain object held by the mediator, transfers
    control to the plugin-specific Process() method, and updates the chain again
    once the processing is complete.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    parser_mediator.AppendToParserChain(self.NAME)

    parser_chain = parser_mediator.GetParserChain()
    parser_mediator.SampleStartTiming(parser_chain)

    try:
      self.Process(parser_mediator, **kwargs)

    finally:
      parser_mediator.SampleStopTiming(parser_chain)

      parser_mediator.PopFromParserChain()


class BasePluginCache(object):
  """A generic cache for parser plugins."""

  def GetResults(self, attribute, default_value=None):
    """Retrieves a cached attribute.

    Args:
      attribute (str): name of the cached attribute.
      default_value (Optional[object]): default value.

    Returns:
      object: value of the cached attribute or default value if the cache
          does not contain the attribute.
    """
    return getattr(self, attribute, default_value)
