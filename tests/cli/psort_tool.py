#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the psort CLI tool."""

from __future__ import unicode_literals

import argparse
import io
import os
import unittest

try:
  import resource
except ImportError:
  resource = None

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
    return 'foobar'


class TestOutputModuleArgumentHelper(helpers_interface.ArgumentsHelper):
  """Test argument helper for the test output module."""

  NAME = 'test_missing'

  @classmethod
  def AddArguments(cls, argument_group):
    """Mock the add argument section."""
    return

  # pylint: disable=arguments-differ
  @classmethod
  def ParseOptions(cls, options, output_module):
    """Provide a test parse options section."""
    if not isinstance(output_module, TestOutputModuleMissingParameters):
      raise errors.BadConfigObject((
          'Output module is not an instance of '
          'TestOutputModuleMissingParameters'))

    missing = getattr(options, 'missing', None)
    if missing:
      output_module.SetMissingValue('missing', missing)

    parameters = getattr(options, 'parameters', None)
    if parameters:
      output_module.SetMissingValue('parameters', parameters)


class TestOutputModuleMissingParameters(output_interface.LinearOutputModule):
  """Test output module that is missing some parameters."""

  NAME = 'test_missing'

  _HEADER = (
      'date,time,timezone,MACB,source,sourcetype,type,user,host,'
      'short,desc,version,filename,inode,notes,format,extra\n')

  # For test purpose assign these as class attributes.
  missing = None
  parameters = None

  def GetMissingArguments(self):
    """Return a list of missing parameters."""
    missing_parameters = []
    if self.missing is None:
      missing_parameters.append('missing')

    if self.parameters is None:
      missing_parameters.append('parameters')

    return missing_parameters

  @classmethod
  def SetMissingValue(cls, attribute, value):
    """Set missing value."""
    setattr(cls, attribute, value)

  def WriteEventBody(self, event, event_data, event_tag):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    message, _ = self._output_mediator.GetFormattedMessages(event_data)
    source_short, source_long = self._output_mediator.GetFormattedSources(
        event, event_data)
    output_text = '{0:s}/{1:s} {2:s}\n'.format(
        source_short, source_long, message)
    self._output_writer.Write(output_text)

  def WriteHeader(self):
    """Writes the header to the output."""
    self._output_writer.Write(self._HEADER)


class PsortToolTest(test_lib.CLIToolTestCase):
  """Tests for the psort tool."""

  if resource is None:
    _EXPECTED_PROCESSING_OPTIONS = """\
usage: psort_test.py [--temporary_directory DIRECTORY]
                     [--worker-memory-limit SIZE]

Test argument parser.

optional arguments:
  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY
                        Path to the directory that should be used to store
                        temporary files created during processing.
  --worker-memory-limit SIZE, --worker_memory_limit SIZE
                        Maximum amount of memory (data segment and shared
                        memory) a worker process is allowed to consume in
                        bytes, where 0 represents no limit. The default limit
                        is 2147483648 (2 GiB). If a worker process exceeds
                        this limit is is killed by the main (foreman) process.
"""
  else:
    _EXPECTED_PROCESSING_OPTIONS = """\
usage: psort_test.py [--process_memory_limit SIZE]
                     [--temporary_directory DIRECTORY]
                     [--worker-memory-limit SIZE]

Test argument parser.

optional arguments:
  --process_memory_limit SIZE, --process-memory-limit SIZE
                        Maximum amount of memory (data segment) a process is
                        allowed to allocate in bytes, where 0 represents no
                        limit. The default limit is 4294967296 (4 GiB). This
                        applies to both the main (foreman) process and the
                        worker processes. This limit is enforced by the
                        operating system and will supersede the worker memory
                        limit (--worker_memory_limit).
  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY
                        Path to the directory that should be used to store
                        temporary files created during processing.
  --worker-memory-limit SIZE, --worker_memory_limit SIZE
                        Maximum amount of memory (data segment and shared
                        memory) a worker process is allowed to consume in
                        bytes, where 0 represents no limit. The default limit
                        is 2147483648 (2 GiB). If a worker process exceeds
                        this limit is is killed by the main (foreman) process.
"""

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
        prog='psort_test.py',
        description='Test argument parser.', add_help=False,
        formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = psort_tool.PsortTool()
    test_tool.AddProcessingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PROCESSING_OPTIONS)

  def testListLanguageIdentifiers(self):
    """Tests the ListLanguageIdentifiers function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psort_tool.PsortTool(output_writer=output_writer)

    test_tool.ListLanguageIdentifiers()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split('\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith('*****') and line.endswith('*****'):
        number_of_tables += 1

    self.assertIn('Language identifiers', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 1)

    expected_line = 'en : English'
    self.assertIn(expected_line, lines)

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psort_tool.PsortTool(output_writer=output_writer)

    result = test_tool.ParseArguments([])
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = test_lib.TestBinaryOutputWriter(encoding='utf-8')
    test_tool = psort_tool.PsortTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.output_format = 'null'
    options.storage_file = self._GetTestFilePath(['psort_test.plaso'])

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options = test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath(['psort_test.plaso'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  def testProcessStorageWithMissingParameters(self):
    """Tests the ProcessStorage function with parameters missing."""
    encoding = 'utf-8'
    input_reader = TestInputReader()
    output_writer = test_lib.TestOutputWriter(encoding=encoding)
    test_tool = psort_tool.PsortTool(
        input_reader=input_reader, output_writer=output_writer)

    options = test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath(['psort_test.plaso'])
    options.output_format = 'test_missing'

    output_manager.OutputManager.RegisterOutput(
        TestOutputModuleMissingParameters)
    helpers_manager.ArgumentHelperManager.RegisterHelper(
        TestOutputModuleArgumentHelper)

    lines = []
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file_name = os.path.join(temp_directory, 'output.txt')
      options.write = temp_file_name

      test_tool.ParseOptions(options)
      test_tool.ProcessStorage()

      with io.open(temp_file_name, 'rt', encoding=encoding) as file_object:
        for line in file_object.readlines():
          lines.append(line.strip())

    self.assertTrue(input_reader.read_called)
    self.assertEqual(TestOutputModuleMissingParameters.missing, 'foobar')
    self.assertEqual(TestOutputModuleMissingParameters.parameters, 'foobar')

    expected_line = (
        'FILE/OS Metadata Modification Time '
        'OS:/tmp/test/test_data/syslog Type: file')
    self.assertIn(expected_line, lines)

    output_manager.OutputManager.DeregisterOutput(
        TestOutputModuleMissingParameters)
    helpers_manager.ArgumentHelperManager.DeregisterHelper(
        TestOutputModuleArgumentHelper)


if __name__ == '__main__':
  unittest.main()
