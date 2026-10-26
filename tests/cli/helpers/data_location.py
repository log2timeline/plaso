#!/usr/bin/env python3
"""Tests for the data location CLI arguments helper."""

import os
import unittest

import plaso

from plaso.cli import tools
from plaso.cli.helpers import data_location
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class DataLocationArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
    """Tests for the data location CLI arguments helper."""

    # pylint: disable=no-member,protected-access

    _EXPECTED_OUTPUT = f"""\
usage: cli_helper.py [--data PATH]

Test argument parser.

{cli_test_lib.ARGPARSE_OPTIONS:s}:
  --data PATH  Path to a directory containing the data files.
"""

    def testAddArguments(self):
        """Tests the AddArguments function."""
        argument_parser = self._GetTestArgumentParser("cli_helper.py")

        data_location.DataLocationArgumentsHelper.AddArguments(argument_parser)

        output = self._RunArgparseFormatHelp(argument_parser)
        self.assertEqual(output, self._EXPECTED_OUTPUT)

    def testParseOptions(self):
        """Tests the ParseOptions function."""
        options = cli_test_lib.TestOptions()
        options.data_location = self._GetTestFilePath(["testdir"])

        test_tool = tools.CLITool()
        data_location.DataLocationArgumentsHelper.ParseOptions(options, test_tool)

        self.assertEqual(test_tool._data_location, options.data_location)

        with self.assertRaises(errors.BadConfigObject):
            data_location.DataLocationArgumentsHelper.ParseOptions(options, None)

        # A data location that does not exist falls back to the data files
        # included with plaso.
        expected_data_location = os.path.join(os.path.dirname(plaso.__file__), "data")

        options.data_location = self._GetTestFilePath(["bogus"])

        data_location.DataLocationArgumentsHelper.ParseOptions(options, test_tool)

        self.assertEqual(test_tool._data_location, expected_data_location)

        options = cli_test_lib.TestOptions()
        test_tool = tools.CLITool()

        data_location.DataLocationArgumentsHelper.ParseOptions(options, test_tool)

        self.assertEqual(test_tool._data_location, expected_data_location)


if __name__ == "__main__":
    unittest.main()
