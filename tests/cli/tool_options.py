#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the CLI tool options mix-ins."""

from __future__ import unicode_literals

import unittest

from plaso.cli import tool_options
from plaso.cli import tools
from plaso.output import manager as output_manager

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class TestToolWithAnalysisPluginOptions(
    tools.CLITool, tool_options.AnalysisPluginOptions):
  """Tool to test the analysis plugin options."""

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(TestToolWithAnalysisPluginOptions, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._analysis_plugins = None


class AnalysisPluginOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the analysis plugin options."""

  # pylint: disable=protected-access

  @shared_test_lib.skipUnlessHasTestFile(['tagging_file', 'valid.txt'])
  def testCreateAnalysisPlugins(self):
    """Tests the _CreateAnalysisPlugins function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = TestToolWithAnalysisPluginOptions(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.tagging_file = self._GetTestFilePath(['tagging_file', 'valid.txt'])

    test_tool._analysis_plugins = 'tagging'
    plugins = test_tool._CreateAnalysisPlugins(options)
    self.assertIn('tagging', plugins.keys())

    test_tool._analysis_plugins = 'bogus'
    plugins = test_tool._CreateAnalysisPlugins(options)
    self.assertEqual(plugins, {})

    test_tool._analysis_plugins = ''
    plugins = test_tool._CreateAnalysisPlugins(options)
    self.assertEqual(plugins, {})

  def testListAnalysisPlugins(self):
    """Tests the ListAnalysisPlugins function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = TestToolWithAnalysisPluginOptions(output_writer=output_writer)

    test_tool.ListAnalysisPlugins()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split('\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith('*****') and line.endswith('*****'):
        number_of_tables += 1

    self.assertIn('Analysis Plugins', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 1)

    expected_line = (
        'browser_search : Analyze browser search entries from events.')
    self.assertIn(expected_line, lines)


class TestToolWithHashersOptions(
    tools.CLITool, tool_options.HashersOptions):
  """Tool to test the hashers options."""


class HashersOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the hashers options."""

  def testListHashers(self):
    """Tests the ListHashers function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = TestToolWithHashersOptions(output_writer=output_writer)

    test_tool.ListHashers()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split('\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith('*****') and line.endswith('*****'):
        number_of_tables += 1

    self.assertIn('Hashers', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 1)

    expected_line = 'md5 : Calculates an MD5 digest hash over input data.'
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
    self.assertIn('dynamic', available_module_names)
    self.assertIn('json', available_module_names)

  def testListOutputModules(self):
    """Tests the ListOutputModules function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = TestToolWithOutputModuleOptions(output_writer=output_writer)

    test_tool.ListOutputModules()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split('\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith('*****') and line.endswith('*****'):
        number_of_tables += 1

    self.assertIn('Output Modules', lines[1])

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
    expected_line = 'rawpy : "raw" (or native) Python output.'
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
    self.assertIn('linux', available_parser_names)

  def testListParsersAndPlugins(self):
    """Tests the ListParsersAndPlugins function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = TestToolWithParsersOptions(output_writer=output_writer)

    test_tool.ListParsersAndPlugins()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split('\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith('*****') and line.endswith('*****'):
        number_of_tables += 1

    self.assertIn('Parsers', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 10)

    expected_line = 'filestat : Parser for file system stat information.'
    self.assertIn(expected_line, lines)

    expected_line = 'bencode_utorrent : Parser for uTorrent bencoded files.'
    self.assertIn(expected_line, lines)

    expected_line = (
        'msie_webcache : Parser for MSIE WebCache ESE database files.')
    self.assertIn(expected_line, lines)

    expected_line = 'olecf_default : Parser for a generic OLECF item.'
    self.assertIn(expected_line, lines)

    expected_line = 'plist_default : Parser for plist files.'
    self.assertIn(expected_line, lines)

    # Note that the expected line is truncated by the cell wrapping in
    # the table.
    expected_line = (
        'chrome_27_history : Parser for Google Chrome 27 and up history SQLite')
    self.assertIn(expected_line, lines)

    expected_line = 'ssh : Parser for SSH syslog entries.'
    self.assertIn(expected_line, lines)

    expected_line = 'winreg_default : Parser for Registry data.'
    self.assertIn(expected_line, lines)


class TestToolWithProfilingOptions(
    tools.CLITool, tool_options.ProfilingOptions):
  """Tool to test the profiling options."""


class ProfilingOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the profiling options."""

  # pylint: disable=protected-access

  def testListProfilers(self):
    """Tests the ListProfilers function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = TestToolWithProfilingOptions(output_writer=output_writer)

    test_tool.ListProfilers()

    string = output_writer.ReadOutput()
    expected_string = (
        '\n'
        '********************************** Profilers '
        '***********************************\n'
        '       Name : Description\n'
        '----------------------------------------'
        '----------------------------------------\n')
    self.assertTrue(string.startswith(expected_string))


class TestToolWithStorageFileOptions(
    tools.CLITool, tool_options.StorageFileOptions):
  """Tool to test the storage file options."""


class StorageFileOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the storage file options."""

  # TODO: add test for _CheckStorageFile


if __name__ == '__main__':
  unittest.main()
