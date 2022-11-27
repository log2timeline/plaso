#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the parsers manager."""

import unittest

from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins

from tests import test_lib as shared_test_lib


class TestParser(interface.BaseParser):
  """Test parser."""

  NAME = 'test_parser'
  DATA_FORMAT = 'Test parser'

  # pylint: disable=unused-argument
  def Parse(self, parser_mediator, **kwargs):
    """Parses the file entry and extracts events.

    Args:
      parser_mediator (ParserMediator): parser mediator.
    """
    return


class TestParserWithPlugins(interface.BaseParser):
  """Test parser with plugins."""

  NAME = 'test_parser_with_plugins'
  DATA_FORMAT = 'Test parser with plugins'

  _plugin_classes = {}

  # pylint: disable=unused-argument
  def Parse(self, parser_mediator, **kwargs):
    """Parses the file entry and extracts events.

    Args:
      parser_mediator (ParserMediator): parser mediator.
    """
    return


class TestPlugin(plugins.BasePlugin):
  """Test plugin."""

  NAME = 'test_plugin'
  DATA_FORMAT = 'Test plugin'

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, **kwargs):
    """Evaluates if this is the correct plugin and processes data accordingly.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      kwargs (dict[str, object]): Depending on the plugin they may require
          different sets of arguments to be able to evaluate whether or not
          this is the correct plugin.

    Raises:
      ValueError: When there are unused keyword arguments.
    """
    return


class ParsersManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the parsers manager."""

  # pylint: disable=protected-access

  # TODO: add tests for CreateSignatureScanner.

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

  # TODO: add tests for GetFormatsWithSignatures.

  def testCheckParserNames(self):
    """Tests the CheckFilterExpression function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    try:
      expression_invalid_and_valid_names = 'non_existent,test_parser'
      expected_valid_elements = set(['test_parser'])
      expected_invalid_elements = set(['non_existent'])
      valid_elements, invalid_elements = (
          manager.ParsersManager.CheckFilterExpression(
              expression_invalid_and_valid_names))
      self.assertEqual(valid_elements, expected_valid_elements)
      self.assertEqual(invalid_elements, expected_invalid_elements)

      expression_invalid_and_valid_names_with_negation = (
          '!test_parser,!non_existent')
      expected_valid_elements = set(['!test_parser'])
      expected_invalid_elements = set(['!non_existent'])
      valid_elements, invalid_elements = (
          manager.ParsersManager.CheckFilterExpression(
              expression_invalid_and_valid_names_with_negation))
      self.assertEqual(valid_elements, expected_valid_elements)
      self.assertEqual(invalid_elements, expected_invalid_elements)

      expression_with_plugins = (
          '!test_parser_with_plugins/test_plugin,'
          'test_parser_with_plugins/non_existent')
      expected_valid_elements = set(['!test_parser_with_plugins/test_plugin'])
      expected_invalid_elements = set(['test_parser_with_plugins/non_existent'])
      valid_elements, invalid_elements = (
          manager.ParsersManager.CheckFilterExpression(expression_with_plugins))
      self.assertEqual(valid_elements, expected_valid_elements)
      self.assertEqual(invalid_elements, expected_invalid_elements)

      none_expression = None
      valid_elements, invalid_elements = (
          manager.ParsersManager.CheckFilterExpression(none_expression))
      self.assertNotEqual(valid_elements, set())
      self.assertEqual(invalid_elements, set())

      all_parser_names = set(manager.ParsersManager._parser_classes.keys())
      self.assertTrue(all_parser_names.issubset(valid_elements))

    # Degister parsers to ensure unrelated tests don't fail.
    finally:
      manager.ParsersManager.DeregisterParser(TestParser)
      manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
      TestParserWithPlugins.DeregisterPlugin(TestPlugin)

  def testGetNamesOfParsersWithPlugins(self):
    """Tests the GetNamesOfParsersWithPlugins function."""
    parsers_names = manager.ParsersManager.GetNamesOfParsersWithPlugins()

    self.assertGreaterEqual(len(parsers_names), 1)

    self.assertIn('winreg', parsers_names)

  def testGetParserPluginsInformation(self):
    """Tests the GetParserPluginsInformation function."""
    plugins_information = manager.ParsersManager.GetParserPluginsInformation()

    self.assertGreaterEqual(len(plugins_information), 1)

    available_parser_names = [name for name, _ in plugins_information]
    self.assertIn('olecf_default', available_parser_names)

  def testGetParserObjects(self):
    """Tests the GetParserObjects function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression='test_parser')
    for parser in parsers.values():
      parser_names.append(parser.NAME)
    self.assertEqual(parser_names, ['test_parser'])

    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression='!test_parser')
    for parser in parsers.values():
      parser_names.append(parser.NAME)
    self.assertNotEqual(len(parser_names), 0)
    self.assertNotIn('test_parser', parser_names)

    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression='test_parser_with_plugins/test_plugin')
    for parser in parsers.values():
      parser_names.append(parser.NAME)
    self.assertEqual(parser_names, ['test_parser_with_plugins'])

    # Test with a parser name, not using plugin names.
    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression='test_parser_with_plugins')
    for parser in parsers.values():
      parser_names.append(parser.NAME)
    self.assertEqual(parser_names, ['test_parser_with_plugins'])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)

  def testGetParsers(self):
    """Tests the _GetParsers function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    parser_names = []
    for _, parser_class in manager.ParsersManager._GetParsers(
        parser_filter_expression='test_parser'):
      parser_names.append(parser_class.NAME)
    self.assertEqual(parser_names, ['test_parser'])

    parser_names = []
    for _, parser_class in manager.ParsersManager._GetParsers(
        parser_filter_expression='!test_parser'):
      parser_names.append(parser_class.NAME)
    self.assertNotEqual(len(parser_names), 0)
    self.assertNotIn('test_parser', parser_names)

    parser_names = []
    for _, parser_class in manager.ParsersManager._GetParsers(
        parser_filter_expression='test_parser_with_plugins/test_plugin'):
      parser_names.append(parser_class.NAME)
    self.assertEqual(parser_names, ['test_parser_with_plugins'])

    # Test with a parser name, not using plugin names.
    parser_names = []
    for _, parser_class in manager.ParsersManager._GetParsers(
        parser_filter_expression='test_parser_with_plugins'):
      parser_names.append(parser_class.NAME)
    self.assertEqual(parser_names, ['test_parser_with_plugins'])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)

  def testGetParsersInformation(self):
    """Tests the GetParsersInformation function."""
    manager.ParsersManager.RegisterParser(TestParser)

    parsers_information = manager.ParsersManager.GetParsersInformation()

    self.assertGreaterEqual(len(parsers_information), 1)

    available_parser_names = [name for name, _ in parsers_information]
    self.assertIn('test_parser', available_parser_names)

    manager.ParsersManager.DeregisterParser(TestParser)

  def testGetPlugins(self):
    """Tests the GetPlugins function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)

    generator = TestParserWithPlugins.GetPlugins()
    plugin_tuples = list(generator)
    self.assertNotEqual(len(plugin_tuples), 0)
    self.assertIsNotNone(plugin_tuples[0])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)

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

  def testGetPluginObjectByName(self):
    """Tests the GetPluginObjectByName function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)

    plugin = TestParserWithPlugins.GetPluginObjectByName('test_plugin')
    self.assertIsNotNone(plugin)

    plugin = TestParserWithPlugins.GetPluginObjectByName('bogus')
    self.assertIsNone(plugin)

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)


if __name__ == '__main__':
  unittest.main()
