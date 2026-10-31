#!/usr/bin/env python3
"""Tests for the filter file CLI arguments helper."""

import os
import sys
import unittest

from plaso.cli import tools
from plaso.cli.helpers import filter_file
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class FilterFileArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
    """Tests for the filter file CLI arguments helper."""

    # pylint: disable=no-member,protected-access

    _PYTHON3_13_OR_LATER = sys.version_info[0:2] >= (3, 13)

    if _PYTHON3_13_OR_LATER:
        _EXPECTED_OUTPUT = f"""\
usage: cli_helper.py [-f FILE_FILTER]

Test argument parser.

{cli_test_lib.ARGPARSE_OPTIONS:s}:
  -f, --filter-file, --filter_file, --file-filter, --file_filter FILE_FILTER
                        List of files to include for targeted collection of
                        files to parse, one line per file path, setup is
                        /path|file - where each element can contain either a
                        variable set in the preprocessing stage or a regular
                        expression.
"""

    else:
        _EXPECTED_OUTPUT = f"""\
usage: cli_helper.py [-f FILE_FILTER]

Test argument parser.

{cli_test_lib.ARGPARSE_OPTIONS:s}:
  -f FILE_FILTER, --filter-file FILE_FILTER, --filter_file FILE_FILTER, --file-filter FILE_FILTER, --file_filter FILE_FILTER
                        List of files to include for targeted collection of
                        files to parse, one line per file path, setup is
                        /path|file - where each element can contain either a
                        variable set in the preprocessing stage or a regular
                        expression.
"""

    def testAddArguments(self):
        """Tests the AddArguments function."""
        argument_parser = self._GetTestArgumentParser("cli_helper.py")

        filter_file.FilterFileArgumentsHelper.AddArguments(argument_parser)

        output = self._RunArgparseFormatHelp(argument_parser)
        self.assertEqual(output, self._EXPECTED_OUTPUT)

    def testParseOptions(self):
        """Tests the ParseOptions function."""
        options = cli_test_lib.TestOptions()
        options.file_filter = self._GetTestFilePath(
            ["filter_files", "format_test.yaml"]
        )

        test_tool = tools.CLITool()
        filter_file.FilterFileArgumentsHelper.ParseOptions(options, test_tool)

        self.assertEqual(test_tool._filter_file, options.file_filter)

        with self.assertRaises(errors.BadConfigObject):
            filter_file.FilterFileArgumentsHelper.ParseOptions(options, None)

        # Test with a filter file that is not a YAML-based filter file.
        options.file_filter = self._GetTestFilePath(["testdir", "filter2.txt"])

        with self.assertRaises(errors.BadConfigOption):
            filter_file.FilterFileArgumentsHelper.ParseOptions(options, test_tool)

        # A filter file that does not exist is looked up in the data location.
        options.file_filter = os.path.join("bogus", "format_test.yaml")

        with self.assertRaises(errors.BadConfigOption):
            filter_file.FilterFileArgumentsHelper.ParseOptions(options, test_tool)

        test_tool._data_location = self._GetTestFilePath(["filter_files"])
        filter_file.FilterFileArgumentsHelper.ParseOptions(options, test_tool)

        expected_filter_file = self._GetTestFilePath(
            ["filter_files", "format_test.yaml"]
        )
        self.assertEqual(test_tool._filter_file, expected_filter_file)

        options.file_filter = os.path.join("bogus", "bogus.txt")

        with self.assertRaises(errors.BadConfigOption):
            filter_file.FilterFileArgumentsHelper.ParseOptions(options, test_tool)

        options = cli_test_lib.TestOptions()

        filter_file.FilterFileArgumentsHelper.ParseOptions(options, test_tool)

        self.assertIsNone(test_tool._filter_file)


if __name__ == "__main__":
    unittest.main()
