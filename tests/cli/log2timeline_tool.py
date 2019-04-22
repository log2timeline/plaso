#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the log2timeline CLI tool."""

from __future__ import unicode_literals

import argparse
import os
import platform
import unittest

try:
  import resource
except ImportError:
  resource = None

from plaso.cli import log2timeline_tool
from plaso.lib import definitions
from plaso.lib import errors
from plaso.storage.sqlite import sqlite_file

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class Log2TimelineToolTest(test_lib.CLIToolTestCase):
  """Tests for the log2timeline CLI tool."""

  # pylint: disable=protected-access

  _BDE_PASSWORD = 'bde-TEST'
  _OUTPUT_ENCODING = 'utf-8'

  if resource is None:
    _EXPECTED_PROCESSING_OPTIONS = ("""\
usage: log2timeline_test.py [--single_process]
                            [--temporary_directory DIRECTORY]
                            [--worker_memory_limit SIZE] [--workers WORKERS]

Test argument parser.

optional arguments:
  --single_process, --single-process
                        Indicate that the tool should run in a single process.
  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY
                        Path to the directory that should be used to store
                        temporary files created during processing.
  --worker_memory_limit SIZE, --worker-memory-limit SIZE
                        Maximum amount of memory (data segment and shared
                        memory) a worker process is allowed to consume in
                        bytes, where 0 represents no limit. The default limit
                        is 2147483648 (2 GiB). If a worker process exceeds
                        this limit is is killed by the main (foreman) process.
  --workers WORKERS     Number of worker processes [defaults to available
                        system CPUs minus one].
""")
  else:
    _EXPECTED_PROCESSING_OPTIONS = ("""\
usage: log2timeline_test.py [--single_process] [--process_memory_limit SIZE]
                            [--temporary_directory DIRECTORY]
                            [--worker_memory_limit SIZE] [--workers WORKERS]

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
  --single_process, --single-process
                        Indicate that the tool should run in a single process.
  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY
                        Path to the directory that should be used to store
                        temporary files created during processing.
  --worker_memory_limit SIZE, --worker-memory-limit SIZE
                        Maximum amount of memory (data segment and shared
                        memory) a worker process is allowed to consume in
                        bytes, where 0 represents no limit. The default limit
                        is 2147483648 (2 GiB). If a worker process exceeds
                        this limit is is killed by the main (foreman) process.
  --workers WORKERS     Number of worker processes [defaults to available
                        system CPUs minus one].
""")

  def _CheckOutput(self, output, expected_output):
    """Compares the output against the expected output.

    The actual processing time is ignored, since it can vary.

    Args:
      output (str): tool output.
      expected_output (list[str]): expected tool output.
    """
    output = output.split('\n')

    self.assertEqual(output[:3], expected_output[:3])
    self.assertTrue(output[3].startswith('Processing time\t\t: '))
    self.assertEqual(output[4:], expected_output[4:])

  def _CreateExtractionOptions(self, source_path, password=None):
    """Create options for testing extraction.

    Args:
      source_path (str): path of the source (test) data.
      password (Optional[str]): password to unlock test data.

    Returns:
      TestOptions: options for testing extraction.
    """
    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.quiet = True
    options.single_process = True
    options.status_view_mode = 'none'
    options.source = source_path

    if password:
      options.credentials = ['password:{0:s}'.format(password)]

    return options

  # TODO: add tests for _CheckStorageFile
  # TODO: add tests for _CreateProcessingConfiguration

  def testGetPluginData(self):
    """Tests the _GetPluginData function."""
    test_tool = log2timeline_tool.Log2TimelineTool()
    test_tool._data_location = self._GetTestFilePath([])

    plugin_info = test_tool._GetPluginData()

    self.assertIn('Hashers', plugin_info)

    available_hasher_names = [name for name, _ in plugin_info['Hashers']]
    self.assertIn('sha256', available_hasher_names)
    self.assertIn('sha1', available_hasher_names)

    self.assertIn('Parsers', plugin_info)
    self.assertIsNotNone(plugin_info['Parsers'])

    self.assertIn('Parser Plugins', plugin_info)
    self.assertIsNotNone(plugin_info['Parser Plugins'])

  def testParseProcessingOptions(self):
    """Tests the _ParseProcessingOptions function."""
    test_tool = log2timeline_tool.Log2TimelineTool()

    options = test_lib.TestOptions()

    test_tool._ParseProcessingOptions(options)

  # TODO: add tests for _PrintProcessingSummary

  def testAddProcessingOptions(self):
    """Tests the AddProcessingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='log2timeline_test.py',
        description='Test argument parser.', add_help=False,
        formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = log2timeline_tool.Log2TimelineTool()
    test_tool.AddProcessingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PROCESSING_OPTIONS)

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    result = test_tool.ParseArguments([])
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['testdir'])
    self._SkipIfPathNotExists(test_file_path)

    yara_rules_path = self._GetTestFilePath(['yara.rules'])
    self._SkipIfPathNotExists(yara_rules_path)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.source = test_file_path
    options.storage_file = 'storage.plaso'
    options.storage_format = definitions.STORAGE_FORMAT_SQLITE
    options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE
    options.yara_rules_path = yara_rules_path

    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)
    test_tool.ParseOptions(options)

    self.assertIsNotNone(test_tool._yara_rules_string)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path

    # ParseOptions will raise if source is not set.
    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.source = test_file_path

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  def testExtractEventsFromSourcesOnDirectory(self):
    """Tests the ExtractEventsFromSources function on a directory."""
    test_file_path = self._GetTestFilePath(['testdir'])
    self._SkipIfPathNotExists(test_file_path)

    options = self._CreateExtractionOptions(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: directory',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourcesOnAPFSImage(self):
    """Tests the ExtractEventsFromSources function on APFS image."""
    test_file_path = self._GetTestFilePath(['apfs.dmg'])
    self._SkipIfPathNotExists(test_file_path)

    options = self._CreateExtractionOptions(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: storage media image',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourcesOnBDEImage(self):
    """Tests the ExtractEventsFromSources function on BDE image."""
    test_file_path = self._GetTestFilePath(['bdetogo.raw'])
    self._SkipIfPathNotExists(test_file_path)

    options = self._CreateExtractionOptions(
        test_file_path, password=self._BDE_PASSWORD)

    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: storage media image',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourcesImage(self):
    """Tests the ExtractEventsFromSources function on single partition image."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    options = self._CreateExtractionOptions(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: storage media image',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourcesPartitionedImage(self):
    """Tests the ExtractEventsFromSources function on multi partition image."""
    # Note that the source file is a RAW (VMDK flat) image.
    test_file_path = self._GetTestFilePath(['multi_partition_image.vmdk'])
    self._SkipIfPathNotExists(test_file_path)

    options = self._CreateExtractionOptions(test_file_path)
    options.partitions = 'all'

    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: storage media image',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourcesOnVSSImage(self):
    """Tests the ExtractEventsFromSources function on VSS image."""
    test_file_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    options = self._CreateExtractionOptions(test_file_path)
    options.vss_stores = 'all'

    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: storage media image',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          'Number of warnings generated while extracting events: 3.',
          '',
          'Use pinfo to inspect warnings in more detail.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourcesOnFile(self):
    """Tests the ExtractEventsFromSources function on a file."""
    test_file_path = self._GetTestFilePath(['System.evtx'])
    self._SkipIfPathNotExists(test_file_path)

    options = self._CreateExtractionOptions(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: single file',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  @unittest.skipIf(platform.system() == 'Windows', 'not supported on Windows')
  @unittest.skipIf(
      platform.release().endswith('Microsoft'),
      'not supported on Windows Subsystem for Linux')
  def testExtractEventsFromSourcesOnLinkToDirectory(self):
    """Tests the ExtractEventsFromSources function on a symlink to directory."""
    test_file_path = self._GetTestFilePath(['link_to_testdir'])
    self._SkipIfPathNotExists(test_file_path)

    options = self._CreateExtractionOptions(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: directory',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  @unittest.skipIf(platform.system() == 'Windows', 'not supported on Windows')
  @unittest.skipIf(
      platform.release().endswith('Microsoft'),
      'not supported on Windows Subsystem for Linux')
  def testExtractEventsFromSourcesOnLinkToFile(self):
    """Tests the ExtractEventsFromSources function on a symlink to file."""
    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    source_path = self._GetTestFilePath(['link_to_System.evtx'])
    options = self._CreateExtractionOptions(source_path)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: single file',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourcesWithFilestat(self):
    """Tests the ExtractEventsFromSources function with filestat parser."""
    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    source_path = self._GetTestFilePath(['test_pe.exe'])
    options = self._CreateExtractionOptions(source_path)
    options.parsers = 'filestat,pe'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_SQLITE
      options.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      storage_file = sqlite_file.SQLiteStorageFile()
      try:
        storage_file.Open(path=options.storage_file, read_only=True)
      except IOError as exception:
        self.fail((
            'Unable to open storage file after processing with error: '
            '{0!s}.').format(exception))

      # There should be 3 filestat and 3 pe parser generated events.
      events = list(storage_file.GetSortedEvents())
      self.assertEqual(len(events), 6)

  def testShowInfo(self):
    """Tests the output of the tool in info mode."""
    output_writer = test_lib.TestOutputWriter(encoding=self._OUTPUT_ENCODING)
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.show_info = True

    test_tool.ParseOptions(options)
    test_tool.ShowInfo()

    output = output_writer.ReadOutput()

    section_headings = [
        'Hashers', 'Parsers', 'Parser Plugins', 'Parser Presets',
        'Versions']
    for heading in section_headings:
      self.assertIn(heading, output)

    self.assertNotIn('<class', output)


if __name__ == '__main__':
  unittest.main()
