#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline CLI tool."""

import argparse
import os
import unittest

from plaso.cli import log2timeline_tool
from plaso.lib import errors
from plaso.output import manager as output_manager
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class Log2TimelineToolTest(test_lib.CLIToolTestCase):
  """Tests for the log2timeline CLI tool."""

  # pylint: disable=protected-access

  _BDE_PASSWORD = u'bde-TEST'

  _EXPECTED_PROCESSING_OPTIONS = u'\n'.join([
      u'usage: log2timeline_test.py [--disable_zeromq] [--single_process]',
      u'                            [--temporary_directory DIRECTORY]',
      (u'                            [--worker-memory-limit SIZE] '
       u'[--workers WORKERS]'),
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --disable_zeromq, --disable-zeromq',
      (u'                        Disable queueing using ZeroMQ. A '
       u'Multiprocessing queue'),
      u'                        will be used instead.',
      u'  --single_process, --single-process',
      (u'                        Indicate that the tool should run in a '
       u'single process.'),
      u'  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY',
      (u'                        Path to the directory that should be used to '
       u'store'),
      u'                        temporary files created during extraction.',
      u'  --worker-memory-limit SIZE, --worker_memory_limit SIZE',
      (u'                        Maximum amount of memory a worker process is '
       u'allowed'),
      u'                        to consume. [defaults to 2 GiB]',
      (u'  --workers WORKERS     The number of worker processes [defaults to '
       u'available'),
      u'                        system CPUs minus one].',
      u''])

  # TODO: add tests for _CheckStorageFile
  # TODO: add tests for _CreateProcessingConfiguration

  def testGetOutputModulesInformation(self):
    """Tests the _GetOutputModulesInformation function."""
    test_tool = log2timeline_tool.Log2TimelineTool()
    modules_info = test_tool._GetOutputModulesInformation()

    self.assertIsNotNone(modules_info)

    available_module_names = [name for name, _ in modules_info]
    self.assertIn(u'dynamic', available_module_names)
    self.assertIn(u'json', available_module_names)

  def testGetPluginData(self):
    """Tests the _GetPluginData function."""
    test_tool = log2timeline_tool.Log2TimelineTool()
    plugin_info = test_tool._GetPluginData()

    self.assertIn(u'Hashers', plugin_info)

    available_hasher_names = [name for name, _ in plugin_info[u'Hashers']]
    self.assertIn(u'sha256', available_hasher_names)
    self.assertIn(u'sha1', available_hasher_names)

    self.assertIn(u'Parsers', plugin_info)
    self.assertIsNotNone(plugin_info[u'Parsers'])

    self.assertIn(u'Parser Plugins', plugin_info)
    self.assertIsNotNone(plugin_info[u'Parser Plugins'])

  def testParseOutputOptions(self):
    """Tests the _ParseOutputOptions function."""
    test_tool = log2timeline_tool.Log2TimelineTool()

    options = test_lib.TestOptions()

    test_tool._ParseOutputOptions(options)

  def testParseProcessingOptions(self):
    """Tests the _ParseProcessingOptions function."""
    test_tool = log2timeline_tool.Log2TimelineTool()

    options = test_lib.TestOptions()

    test_tool._ParseProcessingOptions(options)

  # TODO: add tests for _PrintProcessingSummary

  # TODO: add tests for AddOutputOptions

  def testAddProcessingOptions(self):
    """Tests the AddProcessingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'log2timeline_test.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = log2timeline_tool.Log2TimelineTool()
    test_tool.AddProcessingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PROCESSING_OPTIONS)

  def testListOutputModules(self):
    """Tests the ListOutputModules function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

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

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.source = self._GetTestFilePath([u'testdir'])
    options.output = u'storage.plaso'

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options = test_lib.TestOptions()
    options.source = self._GetTestFilePath([u'testdir'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  def testExtractEventsFromSourcesOnDirectory(self):
    """Tests the ExtractEventsFromSources function on a directory."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'testdir'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
          b'Source type\t: directory',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourcesOnBDEImage(self):
    """Tests the ExtractEventsFromSources function on BDE image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.credentials = [u'password:{0:s}'.format(self._BDE_PASSWORD)]
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'bdetogo.raw'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
          b'Source type\t: storage media image',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourcesImage(self):
    """Tests the ExtractEventsFromSources function on single partition image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'ímynd.dd'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
          b'Source type\t: storage media image',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourcesPartitionedImage(self):
    """Tests the ExtractEventsFromSources function on multi partition image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.partitions = u'all'
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    # Note that the source file is a RAW (VMDK flat) image.
    options.source = self._GetTestFilePath([u'multi_partition_image.vmdk'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
          b'Source type\t: storage media image',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourcesOnVSSImage(self):
    """Tests the ExtractEventsFromSources function on VSS image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'vsstest.qcow2'])
    options.vss_stores = u'all'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
          b'Source type\t: storage media image',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'Number of errors encountered while extracting events: 1.',
          b'',
          b'Use pinfo to inspect errors in more detail.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourcesOnFile(self):
    """Tests the ExtractEventsFromSources function on a file."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'System.evtx'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
          b'Source type\t: single file',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourcesWithFilestat(self):
    """Tests the ExtractEventsFromSources function with filestat parser."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.quiet = True
    options.parsers = u'filestat,pe'
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'test_pe.exe'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      storage_file = storage_zip_file.ZIPStorageFile()
      try:
        storage_file.Open(path=options.output, read_only=True)
      except IOError as exception:
        self.fail((
            u'Unable to open storage file after processing with error: '
            u'{0:s}.').format(exception))

      # There should be 3 filestat and 3 pe parser generated events.
      events = list(storage_file.GetSortedEvents())
      self.assertEqual(len(events), 6)

  def testShowInfo(self):
    """Tests the output of the tool in info mode."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.show_info = True
    test_tool.ParseOptions(options)
    test_tool.ShowInfo()
    output = output_writer.ReadOutput()

    section_headings = [
        u'Parser Presets', u'Hashers', u'Parser Plugins', u'Versions',
        u'Parsers', u'Output Modules']
    for heading in section_headings:
      self.assertIn(heading, output)

    self.assertNotIn(u'<class', output)


if __name__ == '__main__':
  unittest.main()
