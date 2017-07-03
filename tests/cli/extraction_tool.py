#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction tool object."""

import argparse
import unittest

from plaso.cli import extraction_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class ExtractionToolTest(test_lib.CLIToolTestCase):
  """Tests for the extraction tool object."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT_EXTRACTION_OPTIONS = u'\n'.join([
      u'usage: extraction_tool_test.py [--artifact_definitions PATH]',
      (u'                               [--hashers HASHER_LIST] '
       u'[--parsers PARSER_LIST]'),
      u'                               [--preferred_year YEAR] [-p]',
      u'                               [--process_archives]',
      (u'                               [--skip_compressed_streams] '
       u'[--yara_rules PATH]'),
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --artifact_definitions PATH, --artifact-definitions PATH',
      (u'                        Path to a directory containing artifact '
       u'definitions.'),
      (u'                        Artifact definitions can be used to '
       u'describe and'),
      u'                        quickly collect data data of interest, such as',
      u'                        specific files or Windows Registry keys.',
      u'  --hashers HASHER_LIST',
      (u'                        Define a list of hashers to use by the tool. '
       u'This is a'),
      (u'                        comma separated list where each entry is the '
       u'name of a'),
      (u'                        hasher, such as "md5,sha256". "all" '
       u'indicates that all'),
      (u'                        hashers should be enabled. "none" '
       u'disables all'),
      (u'                        hashers. Use "--hashers list" or '
       u'"--info" to list the'),
      u'                        available hashers.',
      u'  --parsers PARSER_LIST',
      (u'                        Define a list of parsers to use by the tool. '
       u'This is a'),
      (u'                        comma separated list where each entry can be '
       u'either a'),
      (u'                        name of a parser or a parser list. Each entry '
       u'can be'),
      (u'                        prepended with an exclamation mark to negate '
       u'the'),
      (u'                        selection (exclude it). The list match is an '
       u'exact'),
      (u'                        match while an individual parser matching is '
       u'a case'),
      (u'                        insensitive substring match, with support for '
       u'glob'),
      (u'                        patterns. Examples would be: "reg" that '
       u'matches the'),
      (u'                        substring "reg" in all parser names or the '
       u'glob'),
      (u'                        pattern "sky[pd]" that would match all '
       u'parsers that'),
      (u'                        have the string "skyp" or "skyd" in its '
       u'name. All'),
      (u'                        matching is case insensitive. Use "--parsers '
       u'list" or'),
      u'                        "--info" to list the available parsers.',
      u'  --preferred_year YEAR, --preferred-year YEAR',
      (u'                        When a format\'s timestamp does not include '
       u'a year,'),
      (u'                        e.g. syslog, use this as the initial year '
       u'instead of'),
      u'                        attempting auto-detection.',
      u'  --process_archives, --process-archives',
      (u'                        Process file entries embedded within archive '
       u'files,'),
      (u'                        such as archive.tar and archive.zip. This '
       u'can make'),
      u'                        processing significantly slower.',
      u'  --skip_compressed_streams, --skip-compressed-streams',
      u'                        Skip processing file content within compressed',
      u'                        streams, such as syslog.gz and syslog.bz2.',
      u'  --yara_rules PATH, --yara-rules PATH',
      (u'                        Path to a file containing Yara rules '
       u'definitions.'),
      (u'  -p, --preprocess      Turn on preprocessing. Preprocessing is '
       u'turned on by'),
      (u'                        default when parsing image files, however if '
       u'a mount'),
      (u'                        point is being parsed then this parameter '
       u'needs to be'),
      u'                        set manually.',
      u''])

  _EXPECTED_PERFORMANCE_OPTIONS = u'\n'.join([
      u'usage: extraction_tool_test.py [--buffer_size BUFFER_SIZE]',
      u'                               [--queue_size QUEUE_SIZE]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      (u'  --buffer_size BUFFER_SIZE, --buffer-size BUFFER_SIZE, '
       u'--bs BUFFER_SIZE'),
      (u'                        The buffer size for the output (defaults to '
       u'196MiB).'),
      u'  --queue_size QUEUE_SIZE, --queue-size QUEUE_SIZE',
      u'                        The maximum number of queued items per worker',
      u'                        (defaults to 125000)',
      u''])

  def testGetParserPresetsInformation(self):
    """Tests the _GetParserPresetsInformation function."""
    test_tool = extraction_tool.ExtractionTool()

    parser_presets_information = test_tool._GetParserPresetsInformation()
    self.assertGreaterEqual(len(parser_presets_information), 1)

    available_parser_names = [name for name, _ in parser_presets_information]
    self.assertIn(u'linux', available_parser_names)

  @shared_test_lib.skipUnlessHasTestFile([u'artifacts'])
  def testParseArtifactDefinitionsOption(self):
    """Tests the _ParseArtifactDefinitionsOption function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])

    test_tool._ParseArtifactDefinitionsOption(options)

  def testParseExtractionOptions(self):
    """Tests the _ParseExtractionOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    test_tool._ParseExtractionOptions(options)

  def testParsePerformanceOptions(self):
    """Tests the _ParsePerformanceOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    test_tool._ParsePerformanceOptions(options)

  def testParseStorageOptions(self):
    """Tests the _ParseStorageOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    test_tool._ParseStorageOptions(options)

  @shared_test_lib.skipUnlessHasTestFile([u'yara.rules'])
  def testParseYaraRulesOption(self):
    """Tests the _ParseYaraRulesOption function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    options.yara_rules_path = self._GetTestFilePath([u'yara.rules'])

    test_tool._ParseYaraRulesOption(options)

  def testAddExtractionOptions(self):
    """Tests the AddExtractionOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'extraction_tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddExtractionOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_EXTRACTION_OPTIONS)

  def testAddPerformanceOptions(self):
    """Tests the AddPerformanceOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'extraction_tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddPerformanceOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PERFORMANCE_OPTIONS)

  def testListHashers(self):
    """Tests the ListHashers function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = extraction_tool.ExtractionTool(output_writer=output_writer)

    test_tool.ListHashers()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    self.assertIn(u'Hashers', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 1)

    expected_line = b'md5 : Calculates an MD5 digest hash over input data.'
    self.assertIn(expected_line, lines)

  def testListParsersAndPlugins(self):
    """Tests the ListParsersAndPlugins function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = extraction_tool.ExtractionTool(output_writer=output_writer)

    test_tool.ListParsersAndPlugins()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    self.assertIn(u'Parsers', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 9)

    expected_line = b'filestat : Parser for file system stat information.'
    self.assertIn(expected_line, lines)

    expected_line = b'bencode_utorrent : Parser for uTorrent bencoded files.'
    self.assertIn(expected_line, lines)

    expected_line = (
        b'msie_webcache : Parser for MSIE WebCache ESE database files.')
    self.assertIn(expected_line, lines)

    expected_line = b'olecf_default : Parser for a generic OLECF item.'
    self.assertIn(expected_line, lines)

    expected_line = b'plist_default : Parser for plist files.'
    self.assertIn(expected_line, lines)

    expected_line = (
        b'chrome_history : Parser for Chrome history SQLite database files.')
    self.assertIn(expected_line, lines)

    expected_line = b'ssh : Parser for SSH syslog entries.'
    self.assertIn(expected_line, lines)

    expected_line = b'winreg_default : Parser for Registry data.'
    self.assertIn(expected_line, lines)

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    # ParseOptions will raise if source is not set.
    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options.source = self._GetTestFilePath([u'ímynd.dd'])

    test_tool.ParseOptions(options)


if __name__ == '__main__':
  unittest.main()
