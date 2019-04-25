#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the parsers manager."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins

from tests import test_lib as shared_test_lib


class TestParser(interface.BaseParser):
  """Test parser."""

  NAME = 'test_parser'
  DESCRIPTION = 'Test parser.'

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
  DESCRIPTION = 'Test parser with plugins.'

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
  DESCRIPTION = 'Test plugin.'

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
    parser_filter_expression = ''
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {})
    self.assertEqual(excludes, {})

    parser_filter_expression = 'test_include,!test_exclude'
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {'test_include': []})
    self.assertEqual(excludes, {})

    parser_filter_expression = (
        'test_include,test_intersection,!test_exclude,!test_intersection')
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {'test_include': []})
    self.assertEqual(excludes, {})

    parser_filter_expression = 'test/include,!test/exclude'
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {'test': ['include']})
    self.assertEqual(excludes, {'test': ['exclude']})

    parser_filter_expression = (
        'test/include,test/intersection,!test/exclude,!test/intersection')
    includes, excludes = manager.ParsersManager._GetParserFilters(
        parser_filter_expression)
    self.assertEqual(includes, {'test': ['include']})
    self.assertEqual(excludes, {'test': ['exclude', 'intersection']})

  def testGetParsersFromPresetCategory(self):
    """Tests the _GetParsersFromPresetCategory function."""
    expected_parser_names = [
        'bencode', 'binary_cookies', 'chrome_cache', 'chrome_preferences',
        'czip/oxml', 'esedb', 'esedb/msie_webcache', 'filestat',
        'firefox_cache', 'gdrive_synclog', 'java_idx', 'lnk',
        'mcafee_protection', 'msiecf', 'olecf', 'opera_global',
        'opera_typed_history', 'pe', 'plist/safari_history', 'prefetch',
        'sccm', 'skydrive_log', 'skydrive_log_old', 'sqlite/chrome_27_history',
        'sqlite/chrome_8_history', 'sqlite/chrome_autofill',
        'sqlite/chrome_cookies', 'sqlite/chrome_extension_activity',
        'sqlite/firefox_cookies', 'sqlite/firefox_downloads',
        'sqlite/firefox_history', 'sqlite/google_drive', 'sqlite/skype',
        'symantec_scanlog', 'usnjrnl', 'winfirewall', 'winjob', 'winreg']

    parser_names = manager.ParsersManager._GetParsersFromPresetCategory(
        'win_gen')
    self.assertEqual(parser_names, expected_parser_names)

    parser_names = manager.ParsersManager._GetParsersFromPresetCategory(
        'bogus')
    self.assertEqual(parser_names, [])

  def testReduceParserFilters(self):
    """Tests the _ReduceParserFilters function."""
    includes = {}
    excludes = {}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {})
    self.assertEqual(excludes, {})

    includes = {'test_include': ''}
    excludes = {'test_exclude': ''}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {'test_include': ''})
    self.assertEqual(excludes, {})

    includes = {'test_include': '', 'test_intersection': ''}
    excludes = {'test_exclude': '', 'test_intersection': ''}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {'test_include': ''})
    self.assertEqual(excludes, {})

    includes = {'test': ['include']}
    excludes = {'test': ['exclude']}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {'test': ['include']})
    self.assertEqual(excludes, {'test': ['exclude']})

    includes = {'test': ['include', 'intersection']}
    excludes = {'test': ['exclude', 'intersection']}

    manager.ParsersManager._ReduceParserFilters(includes, excludes)
    self.assertEqual(includes, {'test': ['include']})
    self.assertEqual(excludes, {'test': ['exclude', 'intersection']})

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

  def testGetNamesOfParsersWithPlugins(self):
    """Tests the GetNamesOfParsersWithPlugins function."""
    parsers_names = manager.ParsersManager.GetNamesOfParsersWithPlugins()

    self.assertGreaterEqual(len(parsers_names), 1)

    self.assertIn('winreg', parsers_names)

  @shared_test_lib.skipUnlessHasTestFile(['presets.yaml'])
  def testGetParserAndPluginNames(self):
    """Tests the GetParserAndPluginNames function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression='test_parser')
    self.assertEqual(parser_names, ['test_parser'])

    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression='!test_parser')
    self.assertNotIn('test_parser', parser_names)

    expected_parser_names = [
        'test_parser_with_plugins',
        'test_parser_with_plugins/test_plugin']
    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression='test_parser_with_plugins/test_plugin')
    self.assertEqual(parser_names, expected_parser_names)

    # Test with a parser name, not using plugin names.
    expected_parser_names = [
        'test_parser_with_plugins',
        'test_parser_with_plugins/test_plugin']
    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression='test_parser_with_plugins')
    self.assertEqual(parser_names, expected_parser_names)

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)

    # Test with a preset name.
    test_path = self._GetTestFilePath(['presets.yaml'])
    manager.ParsersManager.ReadPresetsFromFile(test_path)

    parser_names = manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression='win_gen')
    self.assertIn('lnk', parser_names)

  def testGetParserPluginsInformation(self):
    """Tests the GetParserPluginsInformation function."""
    plugins_information = manager.ParsersManager.GetParserPluginsInformation()

    self.assertGreaterEqual(len(plugins_information), 1)

    available_parser_names = [name for name, _ in plugins_information]
    self.assertIn('olecf_default', available_parser_names)

  def testGetParserObjectByName(self):
    """Tests the GetParserObjectByName function."""
    manager.ParsersManager.RegisterParser(TestParser)

    parser = manager.ParsersManager.GetParserObjectByName(
        'test_parser')
    self.assertIsNotNone(parser)
    self.assertEqual(parser.NAME, 'test_parser')

    parser = manager.ParsersManager.GetParserObjectByName('bogus')
    self.assertIsNone(parser)

    manager.ParsersManager.DeregisterParser(TestParser)

  def testGetParserObjects(self):
    """Tests the GetParserObjects function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression='test_parser')
    for _, parser in iter(parsers.items()):
      parser_names.append(parser.NAME)
    self.assertEqual(parser_names, ['test_parser'])

    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression='!test_parser')
    for _, parser in iter(parsers.items()):
      parser_names.append(parser.NAME)
    self.assertNotEqual(len(parser_names), 0)
    self.assertNotIn('test_parser', parser_names)

    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression='test_parser_with_plugins/test_plugin')
    for _, parser in iter(parsers.items()):
      parser_names.append(parser.NAME)
    self.assertEqual(parser_names, ['test_parser_with_plugins'])

    # Test with a parser name, not using plugin names.
    parser_names = []
    parsers = manager.ParsersManager.GetParserObjects(
        parser_filter_expression='test_parser_with_plugins')
    for _, parser in iter(parsers.items()):
      parser_names.append(parser.NAME)
    self.assertEqual(parser_names, ['test_parser_with_plugins'])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)

  @shared_test_lib.skipUnlessHasTestFile(['presets.yaml'])
  def testGetParsers(self):
    """Tests the GetParsers function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)
    manager.ParsersManager.RegisterParser(TestParserWithPlugins)
    manager.ParsersManager.RegisterParser(TestParser)

    parser_names = []
    for _, parser_class in manager.ParsersManager.GetParsers(
        parser_filter_expression='test_parser'):
      parser_names.append(parser_class.NAME)
    self.assertEqual(parser_names, ['test_parser'])

    parser_names = []
    for _, parser_class in manager.ParsersManager.GetParsers(
        parser_filter_expression='!test_parser'):
      parser_names.append(parser_class.NAME)
    self.assertNotEqual(len(parser_names), 0)
    self.assertNotIn('test_parser', parser_names)

    parser_names = []
    for _, parser_class in manager.ParsersManager.GetParsers(
        parser_filter_expression='test_parser_with_plugins/test_plugin'):
      parser_names.append(parser_class.NAME)
    self.assertEqual(parser_names, ['test_parser_with_plugins'])

    # Test with a parser name, not using plugin names.
    parser_names = []
    for _, parser_class in manager.ParsersManager.GetParsers(
        parser_filter_expression='test_parser_with_plugins'):
      parser_names.append(parser_class.NAME)
    self.assertEqual(parser_names, ['test_parser_with_plugins'])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)
    manager.ParsersManager.DeregisterParser(TestParserWithPlugins)
    manager.ParsersManager.DeregisterParser(TestParser)

    # Test with a preset name.
    test_path = self._GetTestFilePath(['presets.yaml'])
    manager.ParsersManager.ReadPresetsFromFile(test_path)

    expected_parser_names = [
        'bencode', 'binary_cookies', 'chrome_cache', 'chrome_preferences',
        'czip', 'esedb', 'filestat', 'firefox_cache', 'gdrive_synclog',
        'java_idx', 'lnk', 'mcafee_protection', 'msiecf', 'olecf',
        'opera_global', 'opera_typed_history', 'pe', 'plist', 'prefetch',
        'sccm', 'skydrive_log', 'skydrive_log_old', 'sqlite',
        'symantec_scanlog', 'usnjrnl', 'winfirewall', 'winjob', 'winreg']

    parser_names = []
    for _, parser_class in manager.ParsersManager.GetParsers(
        parser_filter_expression='win_gen'):
      parser_names.append(parser_class.NAME)

    self.assertEqual(sorted(parser_names), expected_parser_names)

  def testGetParsersInformation(self):
    """Tests the GetParsersInformation function."""
    manager.ParsersManager.RegisterParser(TestParser)

    parsers_information = manager.ParsersManager.GetParsersInformation()

    self.assertGreaterEqual(len(parsers_information), 1)

    available_parser_names = [name for name, _ in parsers_information]
    self.assertIn('test_parser', available_parser_names)

    manager.ParsersManager.DeregisterParser(TestParser)

  def testGetPresetsInformation(self):
    """Tests the GetPresetsInformation function."""
    presets_file = self._GetTestFilePath(['presets.yaml'])
    manager.ParsersManager.ReadPresetsFromFile(presets_file)

    parser_presets_information = manager.ParsersManager.GetPresetsInformation()
    self.assertGreaterEqual(len(parser_presets_information), 1)

    available_parser_names = [name for name, _ in parser_presets_information]
    self.assertIn('linux', available_parser_names)

  def testGetPlugins(self):
    """Tests the GetPlugins function."""
    TestParserWithPlugins.RegisterPlugin(TestPlugin)

    generator = TestParserWithPlugins.GetPlugins()
    plugin_tuples = list(generator)
    self.assertNotEqual(len(plugin_tuples), 0)
    self.assertIsNotNone(plugin_tuples[0])

    TestParserWithPlugins.DeregisterPlugin(TestPlugin)

  # TODO: add tests for GetPresetsForOperatingSystem.

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
