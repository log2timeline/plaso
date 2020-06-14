#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the extraction tool object."""

from __future__ import unicode_literals

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

  _EXPECTED_PERFORMANCE_OPTIONS = '\n'.join([
      'usage: extraction_tool_test.py [--buffer_size BUFFER_SIZE]',
      '                               [--queue_size QUEUE_SIZE]',
      '',
      'Test argument parser.',
      '',
      'optional arguments:',
      ('  --buffer_size BUFFER_SIZE, --buffer-size BUFFER_SIZE, '
       '--bs BUFFER_SIZE'),
      ('                        The buffer size for the output (defaults to '
       '196MiB).'),
      '  --queue_size QUEUE_SIZE, --queue-size QUEUE_SIZE',
      '                        The maximum number of queued items per worker',
      '                        (defaults to 125000)',
      ''])

  if resource is None:
    _EXPECTED_PROCESSING_OPTIONS = ("""\
usage: extraction_tool_test.py [--single_process]
                               [--temporary_directory DIRECTORY]
                               [--vfs_back_end TYPE]
                               [--worker_memory_limit SIZE]
                               [--workers WORKERS]

Test argument parser.

optional arguments:
  --single_process, --single-process
                        Indicate that the tool should run in a single process.
  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY
                        Path to the directory that should be used to store
                        temporary files created during processing.
  --vfs_back_end TYPE, --vfs-back-end TYPE
                        The preferred dfVFS back-end: "auto" or "tsk".
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
usage: extraction_tool_test.py [--single_process]
                               [--process_memory_limit SIZE]
                               [--temporary_directory DIRECTORY]
                               [--vfs_back_end TYPE]
                               [--worker_memory_limit SIZE]
                               [--workers WORKERS]

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
  --vfs_back_end TYPE, --vfs-back-end TYPE
                        The preferred dfVFS back-end: "auto" or "tsk".
  --worker_memory_limit SIZE, --worker-memory-limit SIZE
                        Maximum amount of memory (data segment and shared
                        memory) a worker process is allowed to consume in
                        bytes, where 0 represents no limit. The default limit
                        is 2147483648 (2 GiB). If a worker process exceeds
                        this limit is is killed by the main (foreman) process.
  --workers WORKERS     Number of worker processes [defaults to available
                        system CPUs minus one].
""")

  _EXPECTED_TIME_ZONE_OPTION = """\
usage: extraction_tool_test.py [-z TIME_ZONE]

Test argument parser.

optional arguments:
  -z TIME_ZONE, --zone TIME_ZONE, --timezone TIME_ZONE
                        preferred time zone of extracted date and time values
                        that are stored without a time zone indicator. The
                        time zone is determined based on the source data where
                        possible otherwise it will default to UTC. Use "list"
                        to see a list of available time zones.
"""

  # TODO: add test for _CreateProcessingConfiguration

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

  def testParseTimeZoneOption(self):
    """Tests the _ParseTimeZoneOption function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    test_tool._ParseTimeZoneOption(options)
    self.assertIsNone(test_tool._preferred_time_zone)

    options.timezone = 'list'
    test_tool._ParseTimeZoneOption(options)
    self.assertIsNone(test_tool._preferred_time_zone)

    options.timezone = 'CET'
    test_tool._ParseTimeZoneOption(options)
    self.assertEqual(test_tool._preferred_time_zone, 'CET')

  # TODO: add test for _PreprocessSources
  # TODO: add test for _ReadParserPresetsFromFile
  # TODO: add test for _SetExtractionParsersAndPlugins
  # TODO: add test for _SetExtractionPreferredTimeZone

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

  def testAddTimeZoneOption(self):
    """Tests the AddTimeZoneOption function."""
    argument_parser = argparse.ArgumentParser(
        prog='extraction_tool_test.py', description='Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddTimeZoneOption(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_TIME_ZONE_OPTION)

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
        'chrome_27_history : Parser for Google Chrome 27 and later history')
    self.assertIn(expected_line, lines)

    expected_line = 'ssh : Parser for SSH syslog entries.'
    self.assertIn(expected_line, lines)

    expected_line = 'winreg_default : Parser for Registry data.'
    self.assertIn(expected_line, lines)


if __name__ == '__main__':
  unittest.main()
