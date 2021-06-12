#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the YARA rules CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import yara_rules
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class YaraRulesArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the YARA rules CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--yara_rules PATH]

Test argument parser.

{0:s}:
  --yara_rules PATH, --yara-rules PATH
                        Path to a file containing Yara rules definitions.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    yara_rules.YaraRulesArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_file_path = self._GetTestFilePath(['rules.yara'])
    self._SkipIfPathNotExists(test_file_path)

    invalid_rules_path = self._GetTestFilePath(['another_file'])
    self._SkipIfPathNotExists(invalid_rules_path)

    unsupported_rules_path = self._GetTestFilePath(['unsupported_rules.yara'])
    self._SkipIfPathNotExists(unsupported_rules_path)

    options = cli_test_lib.TestOptions()
    options.yara_rules_path = test_file_path

    test_tool = tools.CLITool()
    yara_rules.YaraRulesArgumentsHelper.ParseOptions(options, test_tool)

    self.assertIsNotNone(test_tool._yara_rules_string)

    with self.assertRaises(errors.BadConfigObject):
      yara_rules.YaraRulesArgumentsHelper.ParseOptions(options, None)

    options.yara_rules_path = '/tmp/non_existant'
    with self.assertRaises(errors.BadConfigOption):
      yara_rules.YaraRulesArgumentsHelper.ParseOptions(options, test_tool)

    options.yara_rules_path = invalid_rules_path
    with self.assertRaises(errors.BadConfigOption):
      yara_rules.YaraRulesArgumentsHelper.ParseOptions(options, test_tool)

    options.yara_rules_path = unsupported_rules_path
    with self.assertRaises(errors.BadConfigOption):
      yara_rules.YaraRulesArgumentsHelper.ParseOptions(options, test_tool)


if __name__ == '__main__':
  unittest.main()
