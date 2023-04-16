#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the extraction tool object."""

import argparse
import unittest

try:
  import resource
except ImportError:
  resource = None

from plaso.cli import extraction_tool

from tests.cli import test_lib


class ExtractionToolTest(test_lib.CLIToolTestCase):
  """Tests for the extraction tool object."""

  # pylint: disable=protected-access

  _EXPECTED_PERFORMANCE_OPTIONS = """\
usage: extraction_tool_test.py [--buffer_size BUFFER_SIZE]
                               [--queue_size QUEUE_SIZE]

Test argument parser.

{0:s}:
  --buffer_size BUFFER_SIZE, --buffer-size BUFFER_SIZE, --bs BUFFER_SIZE
                        The buffer size for the output (defaults to 196MiB).
  --queue_size QUEUE_SIZE, --queue-size QUEUE_SIZE
                        The maximum number of queued items per worker
                        (defaults to 125000)
""".format(test_lib.ARGPARSE_OPTIONS)

  if resource is None:
    _EXPECTED_PROCESSING_OPTIONS = """\
usage: extraction_tool_test.py [--single_process]
                               [--temporary_directory DIRECTORY]
                               [--vfs_back_end TYPE]
                               [--worker_memory_limit SIZE]
                               [--worker_timeout MINUTES] [--workers WORKERS]

Test argument parser.

{0:s}:
  --single_process, --single-process
                        Indicate that the tool should run in a single process.
  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY
                        Path to the directory that should be used to store
                        temporary files created during processing.
  --vfs_back_end TYPE, --vfs-back-end TYPE
                        The preferred dfVFS back-end: "auto", "fsext",
                        "fsfat", "fshfs", "fsntfs", "tsk" or "vsgpt".
  --worker_memory_limit SIZE, --worker-memory-limit SIZE
                        Maximum amount of memory (data segment and shared
                        memory) a worker process is allowed to consume in
                        bytes, where 0 represents no limit. The default limit
                        is 2147483648 (2 GiB). If a worker process exceeds
                        this limit it is killed by the main (foreman) process.
  --worker_timeout MINUTES, --worker-timeout MINUTES
                        Number of minutes before a worker process that is not
                        providing status updates is considered inactive. The
                        default timeout is 15.0 minutes. If a worker process
                        exceeds this timeout it is killed by the main
                        (foreman) process.
  --workers WORKERS     Number of worker processes. The default is the number
                        of available system CPUs minus one, for the main
                        (foreman) process.
""".format(test_lib.ARGPARSE_OPTIONS)

  else:
    _EXPECTED_PROCESSING_OPTIONS = """\
usage: extraction_tool_test.py [--single_process]
                               [--process_memory_limit SIZE]
                               [--temporary_directory DIRECTORY]
                               [--vfs_back_end TYPE]
                               [--worker_memory_limit SIZE]
                               [--worker_timeout MINUTES] [--workers WORKERS]

Test argument parser.

{0:s}:
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
  --vfs_back_end TYPE, --vfs-back-end TYPE
                        The preferred dfVFS back-end: "auto", "fsext",
                        "fsfat", "fshfs", "fsntfs", "tsk" or "vsgpt".
  --worker_memory_limit SIZE, --worker-memory-limit SIZE
                        Maximum amount of memory (data segment and shared
                        memory) a worker process is allowed to consume in
                        bytes, where 0 represents no limit. The default limit
                        is 2147483648 (2 GiB). If a worker process exceeds
                        this limit it is killed by the main (foreman) process.
  --worker_timeout MINUTES, --worker-timeout MINUTES
                        Number of minutes before a worker process that is not
                        providing status updates is considered inactive. The
                        default timeout is 15.0 minutes. If a worker process
                        exceeds this timeout it is killed by the main
                        (foreman) process.
  --workers WORKERS     Number of worker processes. The default is the number
                        of available system CPUs minus one, for the main
                        (foreman) process.
""".format(test_lib.ARGPARSE_OPTIONS)

  _EXPECTED_TIME_ZONE_OPTION = """\
usage: extraction_tool_test.py [--codepage CODEPAGE] [--language LANGUAGE_TAG]
                               [--no_extract_winevt_resources] [-z TIME_ZONE]

Test argument parser.

{0:s}:
  --codepage CODEPAGE   The preferred codepage, which is used for decoding
                        single-byte or multi-byte character extracted strings.
  --language LANGUAGE_TAG
                        The preferred language, which is used for extracting
                        and formatting Windows EventLog message strings. Use "
                        --language list" to see a list of supported language
                        tags. The en-US (LCID 0x0409) language is used as
                        fallback if preprocessing could not determine the
                        system language or no language information is
                        available in the winevt-rc.db database.
  --no_extract_winevt_resources, --no-extract-winevt-resources
                        Do not extract Windows EventLog resources such as
                        event message template strings. By default Windows
                        EventLog resources will be extracted when a Windows
                        EventLog parser is enabled.
  -z TIME_ZONE, --zone TIME_ZONE, --timezone TIME_ZONE
                        preferred time zone of extracted date and time values
                        that are stored without a time zone indicator. The
                        time zone is determined based on the source data where
                        possible otherwise it will default to UTC. Use "list"
                        to see a list of available time zones.
""".format(test_lib.ARGPARSE_OPTIONS)

  _STORAGE_FILENAME_TEMPLATE = r'\d{{8}}T\d{{6}}-{filename}.plaso'

  # TODO: add test for _CreateProcessingConfiguration

  def testGenerateStorageFileName(self):
    """Tests the _GenerateStorageFileName function."""
    test_tool = extraction_tool.ExtractionTool()

    test_tool._source_path = '/test/storage/path'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='path')
    self.assertRegex(storage_filename, expected_storage_filename)

    test_tool._source_path = '/test/storage/path/'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='path')
    self.assertRegex(storage_filename, expected_storage_filename)

    test_tool._source_path = '/'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='ROOT')
    self.assertRegex(storage_filename, expected_storage_filename)

    test_tool._source_path = '/foo/..'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='ROOT')
    self.assertRegex(storage_filename, expected_storage_filename)

    test_tool._source_path = 'foo/../bar'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='bar')
    self.assertRegex(storage_filename, expected_storage_filename)

  def testParseExtractionOptions(self):
    """Tests the _ParseExtractionOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    test_tool._ParseExtractionOptions(options)
    self.assertIsNone(test_tool._preferred_time_zone)

    options.timezone = 'list'
    test_tool._ParseExtractionOptions(options)
    self.assertIsNone(test_tool._preferred_time_zone)

    options.timezone = 'CET'
    test_tool._ParseExtractionOptions(options)
    self.assertEqual(test_tool._preferred_time_zone, 'CET')

  def testParsePerformanceOptions(self):
    """Tests the _ParsePerformanceOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    test_tool._ParsePerformanceOptions(options)

  def testParseProcessingOptions(self):
    """Tests the _ParseProcessingOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    test_tool._ParseProcessingOptions(options)

  # TODO: add test for _ReadParserPresetsFromFile
  # TODO: add test for _SetExtractionPreferredTimeZone

  def testAddExtractionOptions(self):
    """Tests the AddExtractionOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='extraction_tool_test.py', description='Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddExtractionOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_TIME_ZONE_OPTION)

  def testAddPerformanceOptions(self):
    """Tests the AddPerformanceOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='extraction_tool_test.py', description='Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddPerformanceOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PERFORMANCE_OPTIONS)

  def testAddProcessingOptions(self):
    """Tests the AddProcessingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='extraction_tool_test.py',
        description='Test argument parser.', add_help=False,
        formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddProcessingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PROCESSING_OPTIONS)

  def testListParsersAndPlugins(self):
    """Tests the ListParsersAndPlugins function."""
    presets_file = self._GetTestFilePath(['presets.yaml'])
    self._SkipIfPathNotExists(presets_file)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = extraction_tool.ExtractionTool(output_writer=output_writer)
    test_tool._presets_manager.ReadFromFile(presets_file)

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

    self.assertEqual(number_of_tables, 11)

    expected_line = 'filestat : Parser for file system stat information.'
    self.assertIn(expected_line, lines)

    expected_line = (
        'bencode_utorrent : Parser for uTorrent active torrent files.')
    self.assertIn(expected_line, lines)

    expected_line = (
        'msie_webcache : Parser for Internet Explorer WebCache ESE database')
    self.assertIn(expected_line, lines)

    expected_line = 'olecf_default : Parser for Generic OLE compound item.'
    self.assertIn(expected_line, lines)

    expected_line = 'plist_default : Parser for plist files.'
    self.assertIn(expected_line, lines)

    # Note that the expected line is truncated by the cell wrapping in
    # the table.
    expected_line = (
        'chrome_27_history : Parser for Google Chrome 27 and later history')
    self.assertIn(expected_line, lines)

    expected_line = 'winreg_default : Parser for Windows Registry data.'
    self.assertIn(expected_line, lines)


if __name__ == '__main__':
  unittest.main()
