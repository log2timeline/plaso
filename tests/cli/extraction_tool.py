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

  _EXPECTED_OUTPUT_EXTRACTION_OPTIONS = u'\n'.join([
      (u'usage: extraction_tool_test.py [--hashers HASHER_LIST]'
       u' [--yara_rules PATH]'),
      (u'                               [--parsers PARSER_LIST]'
       u' [--preferred_year YEAR]'),
      u'                               [-p] [--process_archives]',
      u'                               [--skip_compressed_streams]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
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

    # TODO: improve this test.


if __name__ == '__main__':
  unittest.main()
