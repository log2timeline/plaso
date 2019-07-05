#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the extraction tool object."""

from __future__ import unicode_literals

import argparse
import unittest

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

  # TODO: add test for _CreateProcessingConfiguration

  def testParsePerformanceOptions(self):
    """Tests the _ParsePerformanceOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    test_tool._ParsePerformanceOptions(options)

  # TODO: add test for _ParseProcessingOptions
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

  # TODO: add test for AddProcessingOptions

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
        'chrome_27_history : Parser for Google Chrome 27 and up history SQLite')
    self.assertIn(expected_line, lines)

    expected_line = 'ssh : Parser for SSH syslog entries.'
    self.assertIn(expected_line, lines)

    expected_line = 'winreg_default : Parser for Registry data.'
    self.assertIn(expected_line, lines)




if __name__ == '__main__':
  unittest.main()
