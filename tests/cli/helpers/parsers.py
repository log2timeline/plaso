#!/usr/bin/python
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

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--parsers PARSER_LIST]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --parsers PARSER_LIST',
      (u'                        Define a list of parsers to use by the tool. '
       u'This is a'),
      (u'                        comma separated list where each entry can be '
       u'either a'),
      (u'                        name of a parser or a parser list. Each entry '
       u'can be'),
      (u'                        prepended with an exclamation mark to negate '
       u'the'),
      (u'                        selection (exclude it). The list match is an '
       u'exact'),
      (u'                        match while an individual parser matching is '
       u'a case'),
      (u'                        insensitive substring match, with support for '
       u'glob'),
      (u'                        patterns. Examples would be: "reg" that '
       u'matches the'),
      (u'                        substring "reg" in all parser names or the '
       u'glob'),
      (u'                        pattern "sky[pd]" that would match all '
       u'parsers that'),
      (u'                        have the string "skyp" or "skyd" in its '
       u'name. All'),
      (u'                        matching is case insensitive. Use "--parsers '
       u'list" or'),
      u'                        "--info" to list the available parsers.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    parsers.ParsersArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.parsers = u'winevt'

    test_tool = tools.CLITool()
    parsers.ParsersArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._parser_filter_expression, options.parsers)

    with self.assertRaises(errors.BadConfigObject):
      parsers.ParsersArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
