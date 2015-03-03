#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the parsers manager."""

import unittest

from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins


class TestParser(interface.BaseParser):
  """Test parser."""

  NAME = 'test_parser'
  DESCRIPTION = u'Test parser.'

  def Parse(self, unused_parser_mediator, **kwargs):
    """Parsers the file entry and extracts event objects.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
    """
    return


class TestParserWithPlugins(interface.BasePluginsParser):
  """Test parser with plugins."""

  NAME = 'test_parser_with_plugins'
  DESCRIPTION = u'Test parser with plugins.'

  _plugin_classes = {}

  # pylint: disable=unused-argument
  def Parse(self, parser_mediator, **kwargs):
    """Parsers the file entry and extracts event objects.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
    """
    return


class TestPlugin(plugins.BasePlugin):
  """Test plugin."""

  NAME = 'test_plugin'
  DESCRIPTION = u'Test plugin.'

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, **kwargs):
    """Evaluates if this is the correct plugin and processes data accordingly.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      kwargs: Depending on the plugin they may require different sets of
              arguments to be able to evaluate whether or not this is
              the correct plugin.

    Raises:
      ValueError: When there are unused keyword arguments.
    """
    return


class ParsersManagerTest(unittest.TestCase):
  """Tests for the parsers manager."""

  def testParserRegistration(self):
    """Tests the RegisterParser and DeregisterParser functions."""
    # pylint: disable=protected-access
    number_of_parsers = len(manager.ParsersManager._parser_classes)

    manager.ParsersManager.RegisterParser(TestParser)
    self.assertEqual(
        len(manager.ParsersManager._parser_classes),
        number_of_parsers + 1)

    with self.assertRaises(KeyError):
      manager.ParsersManager.RegisterParser(TestParser)

    manager.ParsersManager.DeregisterParser(TestParser)
    self.assertEqual(
        len(manager.ParsersManager._parser_classes),
        number_of_parsers)

  def testPluginRegistration(self):
    """Tests the RegisterPlugin and DeregisterPlugin functions."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    # pylint: disable=protected-access
    self.assertEqual(
        len(TestParserWithPlugins._plugin_classes), 1)

    with self.assertRaises(KeyError):
      TestParserWithPlugins.RegisterPlugin(TestPlugin)

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    self.assertEqual(
        len(TestParserWithPlugins._plugin_classes), 0)

  def testGetFilterListsFromString(self):
    """Tests the GetFilterListsFromString function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    includes, excludes = manager.ParsersManager.GetFilterListsFromString(
        'test_parser')

    self.assertEqual(includes, ['test_parser'])
    self.assertEqual(excludes, [])

    includes, excludes = manager.ParsersManager.GetFilterListsFromString(
        '-test_parser')

    self.assertEqual(includes, [])
    self.assertEqual(excludes, ['test_parser'])

    includes, excludes = manager.ParsersManager.GetFilterListsFromString(
        'test_parser_with_plugins')

    self.assertEqual(includes, ['test_parser_with_plugins', 'test_plugin'])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)


if __name__ == '__main__':
  unittest.main()
