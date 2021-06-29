#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the profiling CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import profiling
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib


class ProfilingArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the profiling CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--profilers PROFILERS_LIST]
                     [--profiling_directory DIRECTORY]
                     [--profiling_sample_rate SAMPLE_RATE]

Test argument parser.

{0:s}:
  --profilers PROFILERS_LIST
                        List of profilers to use by the tool. This is a comma
                        separated list where each entry is the name of a
                        profiler. Use "--profilers list" to list the available
                        profilers.
  --profiling_directory DIRECTORY, --profiling-directory DIRECTORY
                        Path to the directory that should be used to store the
                        profiling sample files. By default the sample files
                        are stored in the current working directory.
  --profiling_sample_rate SAMPLE_RATE, --profiling-sample-rate SAMPLE_RATE
                        Profiling sample rate (defaults to a sample every 1000
                        files).
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    profiling.ProfilingArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    # pylint: disable=no-member

    test_tool = tools.CLITool()

    options = cli_test_lib.TestOptions()
    options.profiling_sample_rate = '100'

    profiling.ProfilingArgumentsHelper.ParseOptions(options, test_tool)
    self.assertEqual(test_tool._profiling_sample_rate, 100)

    with shared_test_lib.TempDirectory() as temp_directory:
      options = cli_test_lib.TestOptions()
      options.profilers = 'processing'
      options.profiling_directory = temp_directory

      profiling.ProfilingArgumentsHelper.ParseOptions(options, test_tool)
      self.assertEqual(test_tool._profilers, set(['processing']))
      self.assertEqual(test_tool._profiling_directory, temp_directory)
      self.assertEqual(test_tool._profiling_sample_rate, 1000)

    with self.assertRaises(errors.BadConfigObject):
      options = cli_test_lib.TestOptions()

      profiling.ProfilingArgumentsHelper.ParseOptions(options, None)

    with self.assertRaises(errors.BadConfigOption):
      options = cli_test_lib.TestOptions()
      options.profilers = 'bogus'

      profiling.ProfilingArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options = cli_test_lib.TestOptions()
      options.profiling_directory = '/bogus'

      profiling.ProfilingArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options = cli_test_lib.TestOptions()
      options.profiling_sample_rate = 'a'

      profiling.ProfilingArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options = cli_test_lib.TestOptions()
      options.profiling_sample_rate = 100

      profiling.ProfilingArgumentsHelper.ParseOptions(options, test_tool)


if __name__ == '__main__':
  unittest.main()
