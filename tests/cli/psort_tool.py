#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psort CLI tool."""

import argparse
import os
import unittest

from plaso.cli import psort_tool
from plaso.cli.helpers import interface as helpers_interface
from plaso.cli.helpers import manager as helpers_manager
from plaso.lib import errors
from plaso.output import interface as output_interface
from plaso.output import manager as output_manager

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


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

  # pylint: disable=arguments-differ
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


class TestOutputModuleMissingParameters(output_interface.LinearOutputModule):
  """Test output module that is missing some parameters."""

  NAME = u'test_missing'

  _HEADER = (
      u'date,time,timezone,MACB,source,sourcetype,type,user,host,'
      u'short,desc,version,filename,inode,notes,format,extra\n')

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

  def WriteEventBody(self, event):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.
    """
    message, _ = self._output_mediator.GetFormattedMessages(event)
    source_short, source_long = self._output_mediator.GetFormattedSources(event)
    self._WriteLine(u'{0:s}/{1:s} {2:s}\n'.format(
        source_short, source_long, message))

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(self._HEADER)


class PsortToolTest(test_lib.CLIToolTestCase):
  """Tests for the psort tool."""

  _EXPECTED_PROCESSING_OPTIONS = u'\n'.join([
      (u'usage: psort_test.py [--disable_zeromq] '
       u'[--temporary_directory DIRECTORY]'),
      u'                     [--worker-memory-limit SIZE]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --disable_zeromq, --disable-zeromq',
      (u'                        Disable queueing using ZeroMQ. A '
       u'Multiprocessing queue'),
      u'                        will be used instead.',
      u'  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY',
      (u'                        Path to the directory that should be used to '
       u'store'),
      u'                        temporary files created during processing.',
      u'  --worker-memory-limit SIZE, --worker_memory_limit SIZE',
      (u'                        Maximum amount of memory a worker process is '
       u'allowed'),
      u'                        to consume. [defaults to 2 GiB]',
      u''])

  # TODO: add test for _CreateOutputModule.
  # TODO: add test for _FormatStatusTableRow.
  # TODO: add test for _GetAnalysisPlugins.
  # TODO: add test for _ParseAnalysisPluginOptions.
  # TODO: add test for _ParseProcessingOptions.
  # TODO: add test for _ParseInformationalOptions.
  # TODO: add test for _PrintStatusHeader.
  # TODO: add test for _PrintStatusUpdate.
  # TODO: add test for _PrintStatusUpdateStream.

  def testAddProcessingOptions(self):
    """Tests the AddProcessingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'psort_test.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = psort_tool.PsortTool()
    test_tool.AddProcessingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PROCESSING_OPTIONS)

  def testListLanguageIdentifiers(self):
    """Tests the ListLanguageIdentifiers function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort_tool.PsortTool(output_writer=output_writer)

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

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort_tool.PsortTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort_tool.PsortTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.output_format = u'null'
    options.storage_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options = test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  def testProcessStorageWithMissingParameters(self):
    """Tests the ProcessStorage function with parameters missing."""
    input_reader = TestInputReader()
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psort_tool.PsortTool(
        input_reader=input_reader, output_writer=output_writer)

    options = test_lib.TestOptions()
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

    expected_line = (
        u'FILE/OS Metadata Modification Time OS:/tmp/test/test_data/syslog '
        u'Type: file')
    self.assertIn(expected_line, lines)

    output_manager.OutputManager.DeregisterOutput(
        TestOutputModuleMissingParameters)
    helpers_manager.ArgumentHelperManager.DeregisterHelper(
        TestOutputModuleArgumentHelper)


if __name__ == '__main__':
  unittest.main()
