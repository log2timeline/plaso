#!/usr/bin/env python3
"""Tests for the log file CLI arguments helper."""

import sys
import unittest

from plaso.cli import psort_tool
from plaso.cli import tools
from plaso.cli.helpers import log_file
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class LogFileArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
    """Tests for the log file CLI arguments helper."""

    # pylint: disable=no-member,protected-access

    _PYTHON3_13_OR_LATER = sys.version_info[0:2] >= (3, 13)

    if _PYTHON3_13_OR_LATER:
        _EXPECTED_OUTPUT = f"""\
usage: cli_helper.py [--logfile FILENAME]

Test argument parser.

{cli_test_lib.ARGPARSE_OPTIONS:s}:
  --logfile, --log_file, --log-file FILENAME
                        Path of the file in which to store log messages, by
                        default this file will be named after the tool, such
                        as: "log2timeline-YYYYMMDDThhmmss.log.gz". Note that
                        the file will be gzip compressed if the extension is
                        ".gz".
"""

    else:
        _EXPECTED_OUTPUT = f"""\
usage: cli_helper.py [--logfile FILENAME]

Test argument parser.

{cli_test_lib.ARGPARSE_OPTIONS:s}:
  --logfile FILENAME, --log_file FILENAME, --log-file FILENAME
                        Path of the file in which to store log messages, by
                        default this file will be named after the tool, such
                        as: "log2timeline-YYYYMMDDThhmmss.log.gz". Note that
                        the file will be gzip compressed if the extension is
                        ".gz".
"""

    def testAddArguments(self):
        """Tests the AddArguments function."""
        argument_parser = self._GetTestArgumentParser("cli_helper.py")

        log_file.LogFileArgumentsHelper.AddArguments(argument_parser)

        output = self._RunArgparseFormatHelp(argument_parser)
        self.assertEqual(output, self._EXPECTED_OUTPUT)

    def testParseOptions(self):
        """Tests the ParseOptions function."""
        options = cli_test_lib.TestOptions()
        options.log_file = "file.log"

        test_tool = tools.CLITool()
        log_file.LogFileArgumentsHelper.ParseOptions(options, test_tool)

        self.assertEqual(test_tool._log_file, "file.log")

        options = cli_test_lib.TestOptions()

        test_tool = psort_tool.PsortTool()
        log_file.LogFileArgumentsHelper.ParseOptions(options, test_tool)

        self.assertRegex(test_tool._log_file, r"^psort-[0-9]{8}T[0-9]{6}\.log\.gz$")

        with self.assertRaises(errors.BadConfigObject):
            log_file.LogFileArgumentsHelper.ParseOptions(options, None)


if __name__ == "__main__":
    unittest.main()
