#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CLI tool options mix-ins."""

import unittest

from plaso.cli import tool_options
from plaso.cli import tools
from plaso.output import manager as output_manager

from tests.cli import test_lib


class TestToolWithAnalysisPluginOptions(
    tools.CLITool, tool_options.AnalysisPluginOptions):
  """Tool to test the analysis plugin options."""


class AnalysisPluginOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the analysis plugin options."""

  def testListAnalysisPlugins(self):
    """Tests the ListAnalysisPlugins function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = TestToolWithAnalysisPluginOptions(output_writer=output_writer)

    test_tool.ListAnalysisPlugins()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    self.assertIn(u'Analysis Plugins', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 1)

    expected_line = (
        b'browser_search : Analyze browser search entries from events.')
    self.assertIn(expected_line, lines)


class TestToolWithHashersOptions(
    tools.CLITool, tool_options.HashersOptions):
  """Tool to test the hashers options."""


class HashersOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the hashers options."""

  def testListHashers(self):
    """Tests the ListHashers function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = TestToolWithHashersOptions(output_writer=output_writer)

    test_tool.ListHashers()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    self.assertIn(u'Hashers', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 1)

    expected_line = b'md5 : Calculates an MD5 digest hash over input data.'
    self.assertIn(expected_line, lines)


class TestToolWithOutputModuleOptions(
    tools.CLITool, tool_options.OutputModuleOptions):
  """Tool to test the output module options."""


class OutputModuleOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the output module options."""

  # pylint: disable=protected-access

  def testGetOutputModulesInformation(self):
    """Tests the _GetOutputModulesInformation function."""
    test_tool = TestToolWithOutputModuleOptions()
    modules_info = test_tool._GetOutputModulesInformation()

    self.assertIsNotNone(modules_info)

    available_module_names = [name for name, _ in modules_info]
    self.assertIn(u'dynamic', available_module_names)
    self.assertIn(u'json', available_module_names)

  def testListOutputModules(self):
    """Tests the ListOutputModules function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = TestToolWithOutputModuleOptions(output_writer=output_writer)

    test_tool.ListOutputModules()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    self.assertIn(u'Output Modules', lines[1])

    lines = frozenset(lines)
    disabled_outputs = list(
        output_manager.OutputManager.GetDisabledOutputClasses())
    enabled_outputs = list(output_manager.OutputManager.GetOutputClasses())

    expected_number_of_tables = 0
    if disabled_outputs:
      expected_number_of_tables += 1
    if enabled_outputs:
      expected_number_of_tables += 1

    self.assertEqual(number_of_tables, expected_number_of_tables)
    expected_line = b'rawpy : "raw" (or native) Python output.'
    self.assertIn(expected_line, lines)


class TestToolWithParsersOptions(
    tools.CLITool, tool_options.ParsersOptions):
  """Tool to test the parsers options."""


class ParsersOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the parsers options."""

  # pylint: disable=protected-access

  def testGetParserPresetsInformation(self):
    """Tests the _GetParserPresetsInformation function."""
    test_tool = TestToolWithParsersOptions()

    parser_presets_information = test_tool._GetParserPresetsInformation()
    self.assertGreaterEqual(len(parser_presets_information), 1)

    available_parser_names = [name for name, _ in parser_presets_information]
    self.assertIn(u'linux', available_parser_names)

  def testListParsersAndPlugins(self):
    """Tests the ListParsersAndPlugins function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = TestToolWithParsersOptions(output_writer=output_writer)

    test_tool.ListParsersAndPlugins()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    self.assertIn(u'Parsers', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 9)

    expected_line = b'filestat : Parser for file system stat information.'
    self.assertIn(expected_line, lines)

    expected_line = b'bencode_utorrent : Parser for uTorrent bencoded files.'
    self.assertIn(expected_line, lines)

    expected_line = (
        b'msie_webcache : Parser for MSIE WebCache ESE database files.')
    self.assertIn(expected_line, lines)

    expected_line = b'olecf_default : Parser for a generic OLECF item.'
    self.assertIn(expected_line, lines)

    expected_line = b'plist_default : Parser for plist files.'
    self.assertIn(expected_line, lines)

    expected_line = (
        b'chrome_history : Parser for Chrome history SQLite database files.')
    self.assertIn(expected_line, lines)

    expected_line = b'ssh : Parser for SSH syslog entries.'
    self.assertIn(expected_line, lines)

    expected_line = b'winreg_default : Parser for Registry data.'
    self.assertIn(expected_line, lines)


class TestToolWithStorageFileOptions(
    tools.CLITool, tool_options.StorageFileOptions):
  """Tool to test the storage file options."""


class StorageFileOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the storage file options."""

  # TODO: add test for _CheckStorageFile


if __name__ == '__main__':
  unittest.main()
