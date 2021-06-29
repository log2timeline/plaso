#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the temporary directory CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import temporary_directory
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class TemporaryDirectoryArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the temporary directory CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--temporary_directory DIRECTORY]

Test argument parser.

{0:s}:
  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY
                        Path to the directory that should be used to store
                        temporary files created during processing.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    temporary_directory.TemporaryDirectoryArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.temporary_directory = self._GetTestFilePath(['testdir'])

    test_tool = tools.CLITool()
    temporary_directory.TemporaryDirectoryArgumentsHelper.ParseOptions(
        options, test_tool)

    self.assertEqual(
        test_tool._temporary_directory, options.temporary_directory)

    with self.assertRaises(errors.BadConfigObject):
      temporary_directory.TemporaryDirectoryArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
