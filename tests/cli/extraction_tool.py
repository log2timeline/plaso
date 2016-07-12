#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction tool object."""

import argparse
import unittest

from plaso.cli import extraction_tool
from plaso.lib import errors

from tests.cli import test_lib


class ExtractionToolTest(test_lib.CLIToolTestCase):
  """Tests for the extraction tool object."""

  _EXPECTED_OUTPUT_EXTRACTION_OPTIONS = u'\n'.join([
      u'usage: extraction_tool_test.py [--hashers HASHER_LIST]',
      u'                               [--yara_rules_path PATH]',
      u'                               [--parsers PARSER_LIST] [-p]',
      u'                               [--process_archives]',
      u'                               [--temporary_directory DIRECTORY]',
      u'                               [--use_old_preprocess]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --hashers HASHER_LIST',
      (u'                        Define a list of hashers to use by the tool. '
       u'This is a'),
      (u'                        comma separated list where each entry is the '
       u'name of a'),
      (u'                        hasher. E.g. "md5,sha256", "all" to indicate '
       u'that all'),
      (u'                        hashers should be enabled or "none" to '
       u'disable all'),
      (u'                        hashers. Use "--hashers list" or "--info" to '
       u'list the'),
      u'                        available hashers.',
      u'  --yara_rules_path PATH, --yara-rules-path PATH',
      (u'                        Path to a file containing Yara rules '
       u'definitions.'),
      u'  --parsers PARSER_LIST',
      (u'                        Define a list of parsers to use by the tool. '
       u'This is a'),
      (u'                        comma separated list where each entry can be '
       u'either a'),
      (u'                        name of a parser or a parser list. Each entry '
       u'can be'),
      (u'                        prepended with a minus sign to negate the '
       u'selection'),
      (u'                        (exclude it). The list match is an exact '
       u'match while'),
      (u'                        an individual parser matching is a case '
       u'insensitive'),
      (u'                        substring match, with support for glob '
       u'patterns.'),
      (u'                        Examples would be: "reg" that matches the '
       u'substring'),
      u'                        "reg" in all parser names or the glob pattern',
      (u'                        "sky[pd]" that would match all parsers that '
       u'have the'),
      (u'                        string "skyp" or "skyd" in its name. All '
       u'matching is'),
      (u'                        case insensitive. Use "--parsers list" or '
       u'"--info" to'),
      u'                        list the available parsers.',
      (u'  -p, --preprocess      Turn on preprocessing. Preprocessing is '
       u'turned on by'),
      (u'                        default when parsing image files, however if '
       u'a mount'),
      (u'                        point is being parsed then this parameter '
       u'needs to be'),
      u'                        set manually.',
      u'  --process_archives, --process-archives',
      (u'                        Process file entries embedded within archive '
       u'files.'),
      (u'                        This can make processing '
       u'significantly slower.'),
      u'  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY',
      (u'                        Path to the directory that should be used to '
       u'store'),
      u'                        temporary files created during extraction.',
      u'  --use_old_preprocess, --use-old-preprocess',
      (u'                        Only used in conjunction when appending to a '
       u'previous'),
      (u'                        storage file. When this option is used then a '
       u'new'),
      (u'                        preprocessing object is not calculated and '
       u'instead the'),
      (u'                        last one that got added to the storage file '
       u'is used.'),
      (u'                        This can be handy when parsing an image that '
       u'contains'),
      u'                        more than a single partition.',
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

  _EXPECTED_PROFILING_OPTIONS = u'\n'.join([
      (u'usage: extraction_tool_test.py [--profile] '
       u'[--profiling_directory DIRECTORY]'),
      u'                               [--profiling_sample_rate SAMPLE_RATE]',
      u'                               [--profiling_type TYPE]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      (u'  --profile             Enable profiling. Intended usage is to '
       u'troubleshoot'),
      u'                        memory and performance issues.',
      u'  --profiling_directory DIRECTORY, --profiling-directory DIRECTORY',
      (u'                        Path to the directory that should be used '
       u'to store the'),
      (u'                        profiling sample files. By default the '
       u'sample files'),
      u'                        are stored in the current working directory.',
      (u'  --profiling_sample_rate SAMPLE_RATE, '
       u'--profiling-sample-rate SAMPLE_RATE'),
      (u'                        The profiling sample rate (defaults to a '
       u'sample every'),
      u'                        1000 files).',
      u'  --profiling_type TYPE, --profiling-type TYPE',
      (u'                        The profiling type: "all", "memory", '
       u'"parsers",'),
      u'                        "processing" or "serializers".',
      u''])

  def testAddExtractionOptions(self):
    """Tests the AddExtractionOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'extraction_tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddExtractionOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_EXTRACTION_OPTIONS)

  def testAddPerformanceOptions(self):
    """Tests the AddPerformanceOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'extraction_tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddPerformanceOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PERFORMANCE_OPTIONS)

  def testAddProfilingOptions(self):
    """Tests the AddProfilingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'extraction_tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddProfilingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PROFILING_OPTIONS)

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
