#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the parsers manager."""

import unittest

from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins

from tests import test_lib as shared_test_lib


class TestParser(interface.BaseParser):
  """Test parser."""

  NAME = u'test_parser'
  DESCRIPTION = u'Test parser.'

  # pylint: disable=unused-argument
  def Parse(self, parser_mediator, **kwargs):
    """Parses the file entry and extracts events.

    Args:
      parser_mediator (ParserMediator): parser mediator.
    """
    return


class TestParserWithPlugins(interface.BaseParser):
  """Test parser with plugins."""

  NAME = u'test_parser_with_plugins'
  DESCRIPTION = u'Test parser with plugins.'

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

  NAME = u'test_plugin'
  DESCRIPTION = u'Test plugin.'

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, **kwargs):
    """Evaluates if this is the correct plugin and processes data accordingly.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      kwargs: Depending on the plugin they may require different sets of
              arguments to be able to evaluate whether or not this is
              the correct plugin.

    Raises:
      ValueError: When there are unused keyword arguments.
    """
    return


class ParsersManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the parsers manager."""

  # pylint: disable=protected-access

  def testGetParserFilters(self):
    """Tests the _GetParserFilters function."""
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

  def testGetParsersFromPresetCategory(self):
    """Tests the _GetParsersFromPresetCategory function."""
    expected_parser_names = [
        u'bencode', u'binary_cookies', u'chrome_cache', u'chrome_preferences',
        u'esedb', u'esedb/msie_webcache', u'filestat', u'firefox_cache',
        u'java_idx', u'lnk', u'mcafee_protection', u'msiecf', u'olecf',
        u'openxml', u'opera_global', u'opera_typed_history', u'pe',
        u'plist/safari_history', u'prefetch', u'sccm', u'skydrive_log',
        u'skydrive_log_old', u'sqlite/chrome_cookies',
        u'sqlite/chrome_extension_activity', u'sqlite/chrome_history',
        u'sqlite/firefox_cookies', u'sqlite/firefox_downloads',
        u'sqlite/firefox_history', u'sqlite/google_drive', u'sqlite/skype',
        u'symantec_scanlog', u'winfirewall', u'winjob', u'winreg']

    parser_names = manager.ParsersManager._GetParsersFromPresetCategory(
        u'win_gen')
    self.assertEqual(parser_names, expected_parser_names)

    parser_names = manager.ParsersManager._GetParsersFromPresetCategory(
        u'bogus')
    self.assertEqual(parser_names, [])

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

  def testGetNamesOfParsersWithPlugins(self):
    """Tests the GetNamesOfParsersWithPlugins function."""
    parsers_names = manager.ParsersManager.GetNamesOfParsersWithPlugins()

    self.assertGreaterEqual(len(parsers_names), 1)

    self.assertIn(u'winreg', parsers_names)

  def testGetParserAndPluginNames(self):
    """Tests the GetParserAndPluginNames function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression=u'test_parser')
    self.assertEqual(parser_names, [u'test_parser'])

    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression=u'!test_parser')
    self.assertNotIn(u'test_parser', parser_names)

    expected_parser_names = [
        u'test_parser_with_plugins',
        u'test_parser_with_plugins/test_plugin']
    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression=u'test_parser_with_plugins/test_plugin')
    self.assertEqual(parser_names, expected_parser_names)

    # Test with a parser name, not using plugin names.
    expected_parser_names = [
        u'test_parser_with_plugins',
        u'test_parser_with_plugins/test_plugin']
    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression=u'test_parser_with_plugins')
    self.assertEqual(parser_names, expected_parser_names)

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)

    # Test with a preset name.
    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression=u'win_gen')
    self.assertIn(u'lnk', parser_names)

  def testGetParserPluginsInformation(self):
    """Tests the GetParserPluginsInformation function."""
    plugins_information = manager.ParsersManager.GetParserPluginsInformation()

    self.assertGreaterEqual(len(plugins_information), 1)

    available_parser_names = [name for name, _ in plugins_information]
    self.assertIn(u'olecf_default', available_parser_names)

  def testGetParserObjectByName(self):
    """Tests the GetParserObjectByName function."""
    manager.ParsersManager.RegisterParser(TestParser)

    parser = manager.ParsersManager.GetParserObjectByName(
        u'test_parser')
    self.assertIsNotNone(parser)
    self.assertEqual(parser.NAME, u'test_parser')

    parser = manager.ParsersManager.GetParserObjectByName(u'bogus')
    self.assertIsNone(parser)

    manager.ParsersManager.DeregisterParser(TestParser)

  def testGetParserObjects(self):
    """Tests the GetParserObjects function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression=u'test_parser')
    for _, parser in iter(parsers.items()):
      parser_names.append(parser.NAME)
    self.assertEqual(parser_names, [u'test_parser'])

    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression=u'!test_parser')
    for _, parser in iter(parsers.items()):
      parser_names.append(parser.NAME)
    self.assertNotEqual(len(parser_names), 0)
    self.assertNotIn(u'test_parser', parser_names)

    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression=u'test_parser_with_plugins/test_plugin')
    for _, parser in iter(parsers.items()):
      parser_names.append(parser.NAME)
    self.assertEqual(parser_names, [u'test_parser_with_plugins'])

    # Test with a parser name, not using plugin names.
    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression=u'test_parser_with_plugins')
    for _, parser in iter(parsers.items()):
      parser_names.append(parser.NAME)
    self.assertEqual(parser_names, [u'test_parser_with_plugins'])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)

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
        parser_filter_expression=u'!test_parser'):
      parser_names.append(parser_class.NAME)
    self.assertNotEqual(len(parser_names), 0)
    self.assertNotIn(u'test_parser', parser_names)

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

    # Test with a preset name.
    expected_parser_names = [
        u'bencode', u'binary_cookies', u'chrome_cache', u'chrome_preferences',
        u'esedb', u'filestat', u'firefox_cache', u'java_idx', u'lnk',
        u'mcafee_protection', u'msiecf', u'olecf', u'openxml', u'opera_global',
        u'opera_typed_history', u'pe', u'plist', u'prefetch', u'sccm',
        u'skydrive_log', u'skydrive_log_old', u'sqlite', u'symantec_scanlog',
        u'winfirewall', u'winjob', u'winreg']

    parser_names = []
    for _, parser_class in manager.ParsersManager.GetParsers(
        parser_filter_expression=u'win_gen'):
      parser_names.append(parser_class.NAME)

    self.assertEqual(sorted(parser_names), expected_parser_names)

  def testGetParsersInformation(self):
    """Tests the GetParsersInformation function."""
    manager.ParsersManager.RegisterParser(TestParser)

    parsers_information = manager.ParsersManager.GetParsersInformation()

    self.assertGreaterEqual(len(parsers_information), 1)

    available_parser_names = [name for name, _ in parsers_information]
    self.assertIn(u'test_parser', available_parser_names)

    manager.ParsersManager.DeregisterParser(TestParser)

  def testGetPlugins(self):
    """Tests the GetPlugins function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)

    generator = TestParserWithPlugins.GetPlugins()
    plugin_tuples = list(generator)
    self.assertNotEqual(len(plugin_tuples), 0)
    self.assertIsNotNone(plugin_tuples[0])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)

  # TODO: add tests for GetPresetForOperatingSystem.
  # TODO: add tests for GetScanner.
  # TODO: add tests for GetSpecificationStore.

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

    plugin = TestParserWithPlugins.GetPluginObjectByName(u'test_plugin')
    self.assertIsNotNone(plugin)

    plugin = TestParserWithPlugins.GetPluginObjectByName(u'bogus')
    self.assertIsNone(plugin)

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)


if __name__ == '__main__':
  unittest.main()
