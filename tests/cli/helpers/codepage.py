#!/usr/bin/env python3
"""Tests for the codepage CLI arguments helper."""

import unittest

from plaso.cli import tools
from plaso.cli.helpers import codepage
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class CodepagergumentsHelperTest(cli_test_lib.CLIToolTestCase):
    """Tests for the codepage CLI arguments helper."""

    # pylint: disable=no-member,protected-access

    _EXPECTED_OUTPUT = f"""\
usage: cli_helper.py [--codepage CODEPAGE]

Test argument parser.

{cli_test_lib.ARGPARSE_OPTIONS:s}:
  --codepage CODEPAGE  The preferred codepage, which is used for decoding
                       single-byte or multi-byte character extracted strings.
"""

    def testAddArguments(self):
        """Tests the AddArguments function."""
        argument_parser = self._GetTestArgumentParser("cli_helper.py")

        codepage.CodepageArgumentsHelper.AddArguments(argument_parser)

        output = self._RunArgparseFormatHelp(argument_parser)
        self.assertEqual(output, self._EXPECTED_OUTPUT)

    def testParseOptions(self):
        """Tests the ParseOptions function."""
        options = cli_test_lib.TestOptions()
        options.preferred_codepage = "cp1252"

        test_tool = tools.CLITool()
        codepage.CodepageArgumentsHelper.ParseOptions(options, test_tool)

        self.assertEqual(test_tool._preferred_codepage, options.preferred_codepage)

        with self.assertRaises(errors.BadConfigObject):
            codepage.CodepageArgumentsHelper.ParseOptions(options, None)


if __name__ == "__main__":
    unittest.main()
