#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the parsers CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import parsers
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class ParsersArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the parsers CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--parsers PARSER_FILTER_EXPRESSION]

Test argument parser.

{0:s}:
  --parsers PARSER_FILTER_EXPRESSION
                        Define which presets, parsers and/or plugins to use,
                        or show possible values. The expression is a comma
                        separated string where each element is a preset,
                        parser or plugin name. Each element can be prepended
                        with an exclamation mark to exclude the item. Matching
                        is case insensitive. Examples: "linux,!bash_history"
                        enables the linux preset, without the bash_history
                        parser. "sqlite,!sqlite/chrome_history" enables all
                        sqlite plugins except for chrome_history".
                        "win7,syslog" enables the win7 preset, as well as the
                        syslog parser. Use "--parsers list" or "--info" to
                        list available presets, parsers and plugins.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    parsers.ParsersArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.parsers = 'winevt'

    test_tool = tools.CLITool()
    parsers.ParsersArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._parser_filter_expression, options.parsers)

    with self.assertRaises(errors.BadConfigObject):
      parsers.ParsersArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
