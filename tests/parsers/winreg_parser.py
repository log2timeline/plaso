#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry file parser."""

import collections
import unittest

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from plaso.engine import artifact_filters
from plaso.engine import knowledge_base as knowledge_base_engine
from plaso.parsers import winreg_parser
# Register all plugins.
from plaso.parsers import winreg_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class WinRegistryParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Registry file parser."""

  # pylint: disable=protected-access

  def _GetParserChains(self, storage_writer):
    """Determines the number of events extracted by a parser plugin.

    Args:
      storage_writer (FakeStorageWriter): storage writer.

    Return:
      collections.Counter: number of events extracted by a parser plugin.
    """
    parser_chains = collections.Counter()
    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      parser_chain = getattr(event_data, 'parser', 'N/A')
      parser_chains[parser_chain] += 1

    return parser_chains

  def _GetParserChainOfPlugin(self, plugin_name):
    """Determines the parser chain of a parser plugin.

    Args:
      plugin_name (str): name of the parser plugin.

    Return:
      str: parser chain of the parser plugin.
    """
    return 'winreg/{0:s}'.format(plugin_name)

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = winreg_parser.WinRegistryParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    # Extract 1 for the default plugin.
    self.assertEqual(len(parser._plugins), number_of_plugins - 1)

    parser.EnablePlugins(['appcompatcache'])
    self.assertEqual(len(parser._plugins), 1)

  def testParse(self):
    """Test the parse function on a Windows NT Registry file."""
    parser = winreg_parser.WinRegistryParser()
    storage_writer = self._ParseFile([
        'regf', '100_sub_keys.hiv'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 101)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseCorruptionInSubKeyList(self):
    """Test the parse function on a corrupted Windows NT Registry file."""
    parser = winreg_parser.WinRegistryParser()
    storage_writer = self._ParseFile([
        'regf', 'corrupt_sub_key_list.hiv'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 100)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseNTUserDat(self):
    """Tests the Parse function on a NTUSER.DAT file."""
    parser = winreg_parser.WinRegistryParser()
    storage_writer = self._ParseFile(['NTUSER.DAT'], parser)

    parser_chains = self._GetParserChains(storage_writer)

    expected_parser_chain = self._GetParserChainOfPlugin('userassist')
    self.assertIn(expected_parser_chain, parser_chains.keys())

    self.assertEqual(parser_chains[expected_parser_chain], 14)

  def testParseNoRootKey(self):
    """Test the parse function on a Registry file with no root key."""
    parser = winreg_parser.WinRegistryParser()
    storage_writer = self._ParseFile(['ntuser.dat.LOG'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseSystem(self):
    """Tests the Parse function on a SYSTEM file."""
    parser = winreg_parser.WinRegistryParser()
    storage_writer = self._ParseFile(['SYSTEM'], parser)

    parser_chains = self._GetParserChains(storage_writer)

    # Check the existence of few known plugins, see if they
    # are being properly picked up and are parsed.
    plugin_names = [
        'windows_usbstor_devices', 'windows_boot_execute',
        'windows_services']
    for plugin in plugin_names:
      expected_parser_chain = self._GetParserChainOfPlugin(plugin)
      self.assertIn(expected_parser_chain, parser_chains.keys())

    # Check that the number of events produced by each plugin are correct.
    parser_chain = self._GetParserChainOfPlugin('windows_usbstor_devices')
    self.assertEqual(parser_chains.get(parser_chain, 0), 10)

    parser_chain = self._GetParserChainOfPlugin('windows_boot_execute')
    self.assertEqual(parser_chains.get(parser_chain, 0), 4)

    parser_chain = self._GetParserChainOfPlugin('windows_services')
    self.assertEqual(parser_chains.get(parser_chain, 0), 831)

  def testParseSystemWithArtifactFilters(self):
    """Tests the Parse function on a SYSTEM file with artifact filters."""
    artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(artifacts_path)

    parser = winreg_parser.WinRegistryParser()
    knowledge_base = knowledge_base_engine.KnowledgeBase()

    artifact_filter_names = ['TestRegistryKey', 'TestRegistryValue']
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    registry.ReadFromDirectory(reader, artifacts_path)

    artifacts_filters_helper = (
        artifact_filters.ArtifactDefinitionsFiltersHelper(
            registry, knowledge_base))

    artifacts_filters_helper.BuildFindSpecs(
        artifact_filter_names, environment_variables=None)

    storage_writer = self._ParseFile(
        ['SYSTEM'], parser, collection_filters_helper=artifacts_filters_helper)

    parser_chains = self._GetParserChains(storage_writer)

    # Check the existence of few known plugins, see if they
    # are being properly picked up and are parsed.
    plugin_names = [
        'windows_usbstor_devices', 'windows_boot_execute',
        'windows_services']
    for plugin in plugin_names:
      expected_parser_chain = self._GetParserChainOfPlugin(plugin)
      self.assertIn(expected_parser_chain, parser_chains.keys())

    # Check that the number of events produced by each plugin are correct.

    # There will be 10 usbstor chains for ControlSet001 and ControlSet002:
    # 'HKEY_LOCAL_MACHINE\System\CurrentControlSet\Enum\USBSTOR'
    parser_chain = self._GetParserChainOfPlugin('windows_usbstor_devices')
    number_of_parser_chains = parser_chains.get(parser_chain, 0)
    self.assertEqual(number_of_parser_chains, 10)

    # There will be 4 Windows boot execute chains for key_value pairs:
    # {key: 'HKEY_LOCAL_MACHINE\System\ControlSet001\Control\Session Manager',
    #     value: 'BootExecute'}
    # {key: 'HKEY_LOCAL_MACHINE\System\ControlSet002\Control\Session Manager',
    #     value: 'BootExecute'}
    parser_chain = self._GetParserChainOfPlugin('windows_boot_execute')
    number_of_parser_chains = parser_chains.get(parser_chain, 0)
    self.assertEqual(number_of_parser_chains, 4)

    # There will be 831 windows services chains for keys:
    # 'HKEY_LOCAL_MACHINE\System\ControlSet001\services\**'
    # 'HKEY_LOCAL_MACHINE\System\ControlSet002\services\**'
    parser_chain = self._GetParserChainOfPlugin('windows_services')
    number_of_parser_chains = parser_chains.get(parser_chain, 0)
    self.assertEqual(number_of_parser_chains, 831)


if __name__ == '__main__':
  unittest.main()
