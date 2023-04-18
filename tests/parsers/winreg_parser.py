#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry file parser."""

import unittest

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from plaso.engine import artifact_filters
from plaso.parsers import winreg_parser
# Register all plugins.
from plaso.parsers import winreg_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class WinRegistryParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Registry file parser."""

  # pylint: disable=protected-access

  def _GetParserChainOfPlugin(self, plugin_name):
    """Determines the parser chain of a parser plugin.

    Args:
      plugin_name (str): name of the parser plugin.

    Return:
      str: parser chain of the parser plugin.
    """
    return 'winreg/{0:s}'.format(plugin_name)

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = winreg_parser.WinRegistryParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins_per_name), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    # Extract 1 for the default plugin.
    self.assertEqual(len(parser._plugins_per_name), number_of_plugins - 1)

    parser.EnablePlugins(['appcompatcache'])
    self.assertEqual(len(parser._plugins_per_name), 1)

  def testParse(self):
    """Test the parse function on a Windows NT Registry file."""
    parser = winreg_parser.WinRegistryParser()
    storage_writer = self._ParseFile([
        'regf', '100_sub_keys.hiv'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 101)

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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 100)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseNTUserDat(self):
    """Tests the Parse function on a NTUSER.DAT file."""
    parser = winreg_parser.WinRegistryParser()
    parser.EnablePlugins(parser.ALL_PLUGINS)
    storage_writer = self._ParseFile(['NTUSER.DAT'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1190)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseNoRootKey(self):
    """Test the parse function on a Registry file with no root key."""
    parser = winreg_parser.WinRegistryParser()
    storage_writer = self._ParseFile(['ntuser.dat.LOG'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseSystem(self):
    """Tests the Parse function on a SYSTEM file."""
    parser = winreg_parser.WinRegistryParser()
    parser.EnablePlugins(parser.ALL_PLUGINS)
    storage_writer = self._ParseFile(['SYSTEM'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 31432)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseSystemWithArtifactFilters(self):
    """Tests the Parse function on a SYSTEM file with artifact filters."""
    artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(artifacts_path)

    parser = winreg_parser.WinRegistryParser()
    parser.EnablePlugins(parser.ALL_PLUGINS)

    artifact_filter_names = ['TestRegistryKey', 'TestRegistryValue']
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    registry.ReadFromDirectory(reader, artifacts_path)

    artifacts_filters_helper = (
        artifact_filters.ArtifactDefinitionsFiltersHelper(registry))

    artifacts_filters_helper.BuildFindSpecs(artifact_filter_names)

    storage_writer = self._ParseFile(
        ['SYSTEM'], parser,
        registry_find_specs=artifacts_filters_helper.registry_find_specs)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3535)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)


if __name__ == '__main__':
  unittest.main()
