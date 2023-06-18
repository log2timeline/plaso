#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the CLI tool options mix-ins."""

import argparse
import unittest

from plaso.cli import tool_options
from plaso.cli import tools
from plaso.output import manager as output_manager

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

  def testCreateAnalysisPlugins(self):
    """Tests the _CreateAnalysisPlugins function."""
    test_file_path = self._GetTestFilePath(['tagging_file', 'valid.txt'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = TestToolWithAnalysisPluginOptions(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.tagging_file = test_file_path

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

  _EXPECTED_OUTPUT_TIME_ZONE_OPTION = """\
usage: tool_options.py [--additional_fields ADDITIONAL_FIELDS]
                       [--custom_fields CUSTOM_FIELDS]
                       [--custom_formatter_definitions PATH] [--dynamic_time]
                       [--output_time_zone TIME_ZONE]

Test argument parser.

{0:s}:
  --additional_fields ADDITIONAL_FIELDS, --additional-fields ADDITIONAL_FIELDS
                        Defines additional fields to be included in the output
                        besides the default fields. Multiple additional field
                        names can be defined as a list of comma separated
                        values. Output formats that support additional fields
                        are: dynamic, opensearch and xlsx.
  --custom_fields CUSTOM_FIELDS, --custom-fields CUSTOM_FIELDS
                        Defines custom fields to be included in the output
                        besides the default fields. A custom field is defined
                        as "name:value". Multiple custom field names can be
                        defined as list of comma separated values. Note that
                        regular fields will are favoured above custom fields
                        with same name. Output formats that support this are:
                        dynamic, opensearch and xlsx.
  --custom_formatter_definitions PATH, --custom-formatter-definitions PATH
                        Path to a file containing custom event formatter
                        definitions, which is a .yaml file. Custom event
                        formatter definitions can be used to customize event
                        messages and override the built-in event formatter
                        definitions.
  --dynamic_time, --dynamic-time
                        Indicate that the output should use dynamic time.
                        Output formats that support dynamic time are: dynamic
  --output_time_zone TIME_ZONE, --output-time-zone TIME_ZONE
                        time zone of date and time values written to the
                        output, if supported by the output format. Use "list"
                        to see a list of available time zones. Output formats
                        that support an output time zone are: dynamic and
                        l2t_csv.
""".format(test_lib.ARGPARSE_OPTIONS)

  def testGetOutputModulesInformation(self):
    """Tests the _GetOutputModulesInformation function."""
    test_tool = TestToolWithOutputModuleOptions()
    modules_info = test_tool._GetOutputModulesInformation()

    self.assertIsNotNone(modules_info)

    available_module_names = [name for name, _ in modules_info]
    self.assertIn('dynamic', available_module_names)
    self.assertIn('json', available_module_names)

  def testParseOutputOptions(self):
    """Tests the _ParseOutputOptions function."""
    test_tool = TestToolWithOutputModuleOptions()

    options = test_lib.TestOptions()

    test_tool._ParseOutputOptions(options)
    self.assertFalse(test_tool._output_dynamic_time)
    self.assertIsNone(test_tool._output_time_zone)

    options.output_time_zone = 'list'
    test_tool._ParseOutputOptions(options)
    self.assertFalse(test_tool._output_dynamic_time)
    self.assertIsNone(test_tool._output_time_zone)

    options.output_time_zone = 'CET'
    test_tool._ParseOutputOptions(options)
    self.assertFalse(test_tool._output_dynamic_time)
    self.assertEqual(test_tool._output_time_zone, 'CET')

  def testAddOutputOptions(self):
    """Tests the AddOutputOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='tool_options.py', description='Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = TestToolWithOutputModuleOptions()
    test_tool.AddOutputOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_TIME_ZONE_OPTION)

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
    expected_line = 'rawpy : native (or "raw") Python output.'
    self.assertIn(expected_line, lines)


class TestToolWithProfilingOptions(
    tools.CLITool, tool_options.ProfilingOptions):
  """Tool to test the profiling options."""


class ProfilingOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the profiling options."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = """\

********************************** Profilers ***********************************
         Name : Description
--------------------------------------------------------------------------------
    analyzers : Profile CPU time of analyzers, like hashing
format_checks : Profile CPU time per format check
       memory : Profile memory usage over time
      parsers : Profile CPU time per parser
   processing : Profile CPU time of processing phases
  serializers : Profile CPU time of serialization
      storage : Profile storage reads and writes
   task_queue : Profile task queue status (multi-processing only)
        tasks : Profile the status of tasks (multi-processing only)
--------------------------------------------------------------------------------
"""

  def testListProfilers(self):
    """Tests the ListProfilers function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = TestToolWithProfilingOptions(output_writer=output_writer)

    test_tool.ListProfilers()

    output = output_writer.ReadOutput()
    self.assertEqual(output, self._EXPECTED_OUTPUT)


class TestToolWithStorageFileOptions(
    tools.CLITool, tool_options.StorageFileOptions):
  """Tool to test the storage file options."""


class StorageFileOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the storage file options."""

  # TODO: add test for _CheckStorageFile


if __name__ == '__main__':
  unittest.main()
