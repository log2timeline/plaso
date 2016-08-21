#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psort CLI tool."""

import argparse
import os
import unittest

from plaso.cli.helpers import interface as helpers_interface
from plaso.cli.helpers import manager as helpers_manager
from plaso.lib import errors
from plaso.output import manager as output_manager

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib
from tests.multi_processing import psort as psort_test

from tools import psort


class TestInputReader(object):
  """Test input reader."""

  def __init__(self):
    """Initialize the reader."""
    super(TestInputReader, self).__init__()
    self.read_called = False

  def Read(self):
    """Mock a read operation by user."""
    self.read_called = True
    return u'foobar'


class TestOutputModuleArgumentHelper(helpers_interface.ArgumentsHelper):
  """Test argument helper for the test output module."""

  NAME = u'test_missing'

  @classmethod
  def AddArguments(cls, argument_group):
    """Mock the add argument section."""
    pass

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Provide a test parse options section."""
    if not isinstance(output_module, TestOutputModuleMissingParameters):
      raise errors.BadConfigObject((
          u'Output module is not an instance of '
          u'TestOutputModuleMissingParameters'))

    missing = getattr(options, u'missing', None)
    if missing:
      output_module.SetMissingValue(u'missing', missing)

    parameters = getattr(options, u'parameters', None)
    if parameters:
      output_module.SetMissingValue(u'parameters', parameters)


class TestOutputModuleMissingParameters(psort_test.TestOutputModule):
  """Test output module that is missing some parameters."""

  NAME = u'test_missing'

  # For test purpose assign these as class attributes.
  missing = None
  parameters = None

  def GetMissingArguments(self):
    """Return a list of missing parameters."""
    missing_parameters = []
    if self.missing is None:
      missing_parameters.append(u'missing')

    if self.parameters is None:
      missing_parameters.append(u'parameters')

    return missing_parameters

  @classmethod
  def SetMissingValue(cls, attribute, value):
    """Set missing value."""
    setattr(cls, attribute, value)


class PsortToolTest(cli_test_lib.CLIToolTestCase):
  """Tests for the psort tool."""

  _EXPECTED_ANALYSIS_PLUGIN_OPTIONS = u'\n'.join([
      u'usage: psort_test.py [--nsrlsvr-host NSRLSVR_HOST]',
      u'                     [--nsrlsvr-port NSRLVR_PORT]',
      u'                     [--virustotal-api-key VIRUSTOTAL_API_KEY]',
      u'                     [--virustotal-free-rate-limit]',
      u'                     [--windows-services-output {text,yaml}]',
      (u'                     [--viper-host VIPER_HOST] [--viper-protocol '
       u'{http,https}]'),
      u'                     [--tagging-file TAGGING_FILE]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --nsrlsvr-host NSRLSVR_HOST',
      u'                        Specify the host to query Nsrlsvr on.',
      u'  --nsrlsvr-port NSRLVR_PORT',
      u'                        Port to use to query Nsrlsvr.',
      u'  --virustotal-api-key VIRUSTOTAL_API_KEY',
      u'                        Specify the API key for use with VirusTotal.',
      u'  --virustotal-free-rate-limit',
      (u'                        Limit Virustotal requests to the default '
       u'free API key'),
      (u'                        rate of 4 requests per minute. Set this to '
       u'false if'),
      u'                        you have an key for the private API.',
      u'  --windows-services-output {text,yaml}',
      (u'                        Specify how the results should be displayed. '
       u'Options'),
      u'                        are text and yaml.',
      u'  --viper-host VIPER_HOST',
      u'                        Specify the host to query Viper on.',
      u'  --viper-protocol {http,https}',
      u'                        Protocol to use to query Viper.',
      u'  --tagging-file TAGGING_FILE, --tagging_file TAGGING_FILE',
      u'                        Specify a file to read tagging criteria from.',
      u''])

  _EXPECTED_EXPERIMENTAL_OPTIONS = u'\n'.join([
      u'usage: psort_test.py [--use_zeromq CHOICE]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --use_zeromq CHOICE  Enables or disables queueing using ZeroMQ',
      u''])

  _EXPECTED_FILTER_OPTIONS = u'\n'.join([
      (u'usage: psort_test.py [--slice DATE] [--slice_size SLICE_SIZE] '
       u'[--slicer]'),
      u'                     [FILTER]',
      u'',
      u'Test argument parser.',
      u'',
      u'positional arguments:',
      (u'  FILTER                A filter that can be used to filter the '
       u'dataset before'),
      (u'                        it is written into storage. More information '
       u'about the'),
      (u'                        filters and how to use them can be found '
       u'here:'),
      (u'                        '
       u'https://github.com/log2timeline/plaso/wiki/Filters'),
      u'',
      u'optional arguments:',
      (u'  --slice DATE          Create a time slice around a certain date. '
       u'This'),
      (u'                        parameter, if defined will display all '
       u'events that'),
      (u'                        happened X minutes before and after the '
       u'defined date.'),
      (u'                        X is controlled by the parameter '
       u'--slice_size but'),
      u'                        defaults to 5 minutes.',
      u'  --slice_size SLICE_SIZE, --slice-size SLICE_SIZE',
      (u'                        Defines the slice size. In the case of a '
       u'regular time'),
      (u'                        slice it defines the number of minutes the '
       u'slice size'),
      (u'                        should be. In the case of the --slicer it '
       u'determines'),
      (u'                        the number of events before and after a '
       u'filter match'),
      (u'                        has been made that will be included in the '
       u'result set.'),
      (u'                        The default value is 5]. See --slice or '
       u'--slicer for'),
      u'                        more details about this option.',
      (u'  --slicer              Create a time slice around every filter '
       u'match. This'),
      (u'                        parameter, if defined will save all X '
       u'events before'),
      (u'                        and after a filter match has been made. X '
       u'is defined'),
      u'                        by the --slice_size parameter.',
      u''])

  _EXPECTED_LANGUAGE_OPTIONS = u'\n'.join([
      u'usage: psort_test.py [--language LANGUAGE]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      (u'  --language LANGUAGE  The preferred language identifier for Windows '
       u'Event Log'),
      (u'                       message strings. Use "--language list" to see '
       u'a list of'),
      (u'                       available language identifiers. Note that '
       u'formatting'),
      (u'                       will fall back on en-US (LCID 0x0409) if the '
       u'preferred'),
      (u'                       language is not available in the database of '
       u'message'),
      u'                       string templates.',
      u''])

  _EXPECTED_OUTPUT_MODULE_OPTIONS = u'\n'.join([
      (u'usage: psort_test.py [--fields FIELDS] '
       u'[--additional_fields ADDITIONAL_FIELDS]'),
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      (u'  --fields FIELDS       Defines which fields should be included in '
       u'the output.'),
      u'  --additional_fields ADDITIONAL_FIELDS',
      (u'                        Defines extra fields to be included in the '
       u'output, in'),
      (u'                        addition to the default fields, which are '
       u'datetime,tim'),
      (u'                        estamp_desc,source,source_long,message,parser,'
       u'display_'),
      u'                        name,tag.',
      u''])

  # TODO: add test for _FormatStatusTableRow.
  # TODO: add test for _ParseAnalysisPluginOptions.
  # TODO: add test for _ParseExperimentalOptions.
  # TODO: add test for _ParseFilterOptions.
  # TODO: add test for _ParseInformationalOptions.
  # TODO: add test for _ParseLanguageOptions.
  # TODO: add test for _PrintStatusHeader.
  # TODO: add test for _PrintStatusUpdate.
  # TODO: add test for _PrintStatusUpdateStream.
  # TODO: add test for _PromptUserForInput.

  def testAddAnalysisPluginOptions(self):
    """Tests the AddAnalysisPluginOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'psort_test.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = psort.PsortTool()
    test_tool.AddAnalysisPluginOptions(argument_parser, [])

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_ANALYSIS_PLUGIN_OPTIONS)

  def testAddExperimentalOptions(self):
    """Tests the AddExperimentalOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'psort_test.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = psort.PsortTool()
    test_tool.AddExperimentalOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_EXPERIMENTAL_OPTIONS)

  def testAddFilterOptions(self):
    """Tests the AddFilterOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'psort_test.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = psort.PsortTool()
    test_tool.AddFilterOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_FILTER_OPTIONS)

  def testAddLanguageOptions(self):
    """Tests the AddLanguageOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'psort_test.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = psort.PsortTool()
    test_tool.AddLanguageOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_LANGUAGE_OPTIONS)

  def testAddOutputModuleOptions(self):
    """Tests the AddOutputModuleOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'psort_test.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = psort.PsortTool()
    test_tool.AddOutputModuleOptions(argument_parser, [u'dynamic'])

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_MODULE_OPTIONS)

  def testListAnalysisPlugins(self):
    """Tests the ListAnalysisPlugins function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort.PsortTool(output_writer=output_writer)

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

  def testListLanguageIdentifiers(self):
    """Tests the ListLanguageIdentifiers function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort.PsortTool(output_writer=output_writer)

    test_tool.ListLanguageIdentifiers()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    self.assertIn(u'Language identifiers', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 1)

    expected_line = b'en : English'
    self.assertIn(expected_line, lines)

  def testListOutputModules(self):
    """Tests the ListOutputModules function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort.PsortTool(output_writer=output_writer)

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

    self.assertEqual(number_of_tables, 2)

    expected_line = b'rawpy : "raw" (or native) Python output.'
    self.assertIn(expected_line, lines)

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort.PsortTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort.PsortTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.output_format = u'null'
    options.storage_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    test_tool.ParseOptions(options)

    options = cli_test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options = cli_test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  def testProcessStorageWithMissingParameters(self):
    """Test the ProcessStorage function with half-configured output module."""
    input_reader = TestInputReader()
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort.PsortTool(
        input_reader=input_reader, output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    options.output_format = u'test_missing'

    output_manager.OutputManager.RegisterOutput(
        TestOutputModuleMissingParameters)
    helpers_manager.ArgumentHelperManager.RegisterHelper(
        TestOutputModuleArgumentHelper)

    lines = []
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file_name = os.path.join(temp_directory, u'output.txt')
      options.write = temp_file_name

      test_tool.ParseOptions(options)
      test_tool.ProcessStorage()

      with open(temp_file_name, 'rb') as file_object:
        for line in file_object.readlines():
          lines.append(line.strip())

    self.assertTrue(input_reader.read_called)
    self.assertEqual(TestOutputModuleMissingParameters.missing, u'foobar')
    self.assertEqual(TestOutputModuleMissingParameters.parameters, u'foobar')

    expected_line = u'FILE/OS ctime OS:/tmp/test/test_data/syslog Type: file'
    self.assertIn(expected_line, lines)

    output_manager.OutputManager.DeregisterOutput(
        TestOutputModuleMissingParameters)
    helpers_manager.ArgumentHelperManager.DeregisterHelper(
        TestOutputModuleArgumentHelper)


if __name__ == '__main__':
  unittest.main()
