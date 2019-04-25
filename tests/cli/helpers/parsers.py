#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the parsers CLI arguments helper."""

from __future__ import unicode_literals

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
usage: cli_helper.py [--parsers PARSER_LIST]

Test argument parser.

optional arguments:
  --parsers PARSER_LIST
                        Define a list of parsers to use by the tool. This is a
                        comma separated list where each entry can be either a
                        name of a parser or a parser list. Each entry can be
                        prepended with an exclamation mark to negate the
                        selection (exclude it). The list match is an exact
                        match while an individual parser matching is a case
                        insensitive substring match, with support for glob
                        patterns. Examples would be: "reg" that matches the
                        substring "reg" in all parser names or the glob
                        pattern "sky[pd]" that would match all parsers that
                        have the string "skyp" or "skyd" in its name. All
                        matching is case insensitive. Use "--parsers list" or
                        "--info" to list the available parsers.
"""

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
