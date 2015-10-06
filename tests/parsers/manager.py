#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the parsers manager."""

import unittest

from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins


class TestParser(interface.BaseParser):
  """Test parser."""

  NAME = u'test_parser'
  DESCRIPTION = u'Test parser.'

  def Parse(self, unused_parser_mediator, **kwargs):
    """Parsers the file entry and extracts event objects.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    return


class TestParserWithPlugins(interface.BaseParser):
  """Test parser with plugins."""

  NAME = u'test_parser_with_plugins'
  DESCRIPTION = u'Test parser with plugins.'

  _plugin_classes = {}

  # pylint: disable=unused-argument
  def Parse(self, parser_mediator, **kwargs):
    """Parsers the file entry and extracts event objects.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    return


class TestPlugin(plugins.BasePlugin):
  """Test plugin."""

  NAME = u'test_plugin'
  DESCRIPTION = u'Test plugin.'

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, **kwargs):
    """Evaluates if this is the correct plugin and processes data accordingly.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
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
        u'test_parser')

    self.assertEqual(includes, [u'test_parser'])
    self.assertEqual(excludes, [])

    includes, excludes = manager.ParsersManager.GetFilterListsFromString(
        u'-test_parser')

    self.assertEqual(includes, [])
    self.assertEqual(excludes, [u'test_parser'])

    includes, excludes = manager.ParsersManager.GetFilterListsFromString(
        u'test_parser_with_plugins')

    self.assertEqual(includes, [u'test_parser_with_plugins', u'test_plugin'])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)

  def testGetParsers(self):
    """Tests the GetParsers function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    # Add a plugin, the parser name should be included.
    test_filter_string = u'test_plugin,test_parser'
    expected_set = set([u'test_parser', u'test_parser_with_plugins'])
    parser_set = set([name for name, _ in list(
        manager.ParsersManager.GetParsers(
            parser_filter_string=test_filter_string))])
    self.assertSetEqual(parser_set, expected_set)

    # Test with a parser name, not using plugin names.
    test_filter_string = u'test_parser_with_plugins'
    expected_set = set([u'test_parser_with_plugins'])
    parser_set = set([name for name, _ in list(
        manager.ParsersManager.GetParsers(
            parser_filter_string=test_filter_string))])
    self.assertSetEqual(parser_set, expected_set)

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)


if __name__ == '__main__':
  unittest.main()
