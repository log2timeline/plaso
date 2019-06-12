#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the YARA rules CLI arguments helper."""

from __future__ import unicode_literals

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

optional arguments:
  --yara_rules PATH, --yara-rules PATH
                        Path to a file containing Yara rules definitions.
"""

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
    test_file_path = self._GetTestFilePath(['yara.rules'])
    self._SkipIfPathNotExists(test_file_path)

    options = cli_test_lib.TestOptions()
    options.yara_rules_path = test_file_path

    test_tool = tools.CLITool()
    yara_rules.YaraRulesArgumentsHelper.ParseOptions(options, test_tool)

    self.assertIsNotNone(test_tool._yara_rules_string)

    with self.assertRaises(errors.BadConfigObject):
      yara_rules.YaraRulesArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
