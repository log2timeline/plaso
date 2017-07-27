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


class TestToolWithStorageFileOptions(
    tools.CLITool, tool_options.StorageFileOptions):
  """Tool to test the storage file options."""


class StorageFileOptionsTest(test_lib.CLIToolTestCase):
  """Tests for the storage file options."""

  # TODO: add test for _CheckStorageFile


if __name__ == '__main__':
  unittest.main()
