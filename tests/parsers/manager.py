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

  # pylint: disable=unused-argument
  def Parse(self, parser_mediator, **kwargs):
    """Parses the file entry and extracts event objects.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
    """
    return


class TestParserWithPlugins(interface.BaseParser):
  """Test parser with plugins."""

  NAME = u'test_parser_with_plugins'
  DESCRIPTION = u'Test parser with plugins.'

  _plugin_classes = {}

  # pylint: disable=unused-argument
  def Parse(self, parser_mediator, **kwargs):
    """Parses the file entry and extracts event objects.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
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

  # pylint: disable=protected-access

  def testGetParserFilters(self):
    """Tests the GetParserFilters function."""
    parser_filter_expression = u''
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {})
    self.assertEqual(excludes, {})

    parser_filter_expression = u'test_include,!test_exclude'
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {u'test_include': []})
    self.assertEqual(excludes, {})

    parser_filter_expression = (
        u'test_include,test_intersection,!test_exclude,!test_intersection')
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {u'test_include': []})
    self.assertEqual(excludes, {})

    parser_filter_expression = u'test/include,!test/exclude'
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {u'test': [u'include']})
    self.assertEqual(excludes, {u'test': [u'exclude']})

    parser_filter_expression = (
        u'test/include,test/intersection,!test/exclude,!test/intersection')
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {u'test': [u'include']})
    self.assertEqual(excludes, {u'test': [u'exclude', u'intersection']})

  def testReduceParserFilters(self):
    """Tests the ReduceParserFilters function."""
    includes = {}
    excludes = {}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {})
    self.assertEqual(excludes, {})

    includes = {u'test_include': u''}
    excludes = {u'test_exclude': u''}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {u'test_include': u''})
    self.assertEqual(excludes, {})

    includes = {u'test_include': u'', u'test_intersection': u''}
    excludes = {u'test_exclude': u'', u'test_intersection': u''}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {u'test_include': u''})
    self.assertEqual(excludes, {})

    includes = {u'test': [u'include']}
    excludes = {u'test': [u'exclude']}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {u'test': [u'include']})
    self.assertEqual(excludes, {u'test': [u'exclude']})

    includes = {u'test': [u'include', u'intersection']}
    excludes = {u'test': [u'exclude', u'intersection']}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {u'test': [u'include']})
    self.assertEqual(excludes, {u'test': [u'exclude', u'intersection']})

  def testParserRegistration(self):
    """Tests the RegisterParser and DeregisterParser functions."""
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
    self.assertEqual(
        len(TestParserWithPlugins._plugin_classes), 1)

    with self.assertRaises(KeyError):
      TestParserWithPlugins.RegisterPlugin(TestPlugin)

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    self.assertEqual(
        len(TestParserWithPlugins._plugin_classes), 0)

  def testGetParsers(self):
    """Tests the GetParsers function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    parser_names = []
    for _, parser_class in manager.ParsersManager.GetParsers(
        parser_filter_expression=u'test_parser'):
      parser_names.append(parser_class.NAME)
    self.assertEqual(parser_names, [u'test_parser'])

    parser_names = []
    for _, parser_class in manager.ParsersManager.GetParsers(
        parser_filter_expression=u'test_parser_with_plugins/test_plugin'):
      parser_names.append(parser_class.NAME)
    self.assertEqual(parser_names, [u'test_parser_with_plugins'])

    # Test with a parser name, not using plugin names.
    parser_names = []
    for _, parser_class in manager.ParsersManager.GetParsers(
        parser_filter_expression=u'test_parser_with_plugins'):
      parser_names.append(parser_class.NAME)
    self.assertEqual(parser_names, [u'test_parser_with_plugins'])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)

  def testGetPluginObjectByName(self):
    """Tests the GetPluginObjectByName function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)

    plugin_object = TestParserWithPlugins.GetPluginObjectByName(u'test_plugin')
    self.assertIsNotNone(plugin_object)

    plugin_object = TestParserWithPlugins.GetPluginObjectByName(u'bogus')
    self.assertIsNone(plugin_object)

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)

  def testGetPlugins(self):
    """Tests the GetPlugins function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)

    generator = TestParserWithPlugins.GetPlugins()
    plugin_tuples = list(generator)
    self.assertNotEqual(len(plugin_tuples), 0)
    self.assertIsNotNone(plugin_tuples[0])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)


if __name__ == '__main__':
  unittest.main()
