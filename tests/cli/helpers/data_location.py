#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the data location CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import data_location
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class DataLocationArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the data location CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--data PATH]

Test argument parser.

{0:s}:
  --data PATH  Path to a directory containing the data files.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    data_location.DataLocationArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.data_location = self._GetTestFilePath(['testdir'])

    test_tool = tools.CLITool()
    data_location.DataLocationArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._data_location, options.data_location)

    with self.assertRaises(errors.BadConfigObject):
      data_location.DataLocationArgumentsHelper.ParseOptions(options, None)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
