#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the YARA rules CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import yara_rules
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib


class YaraRulesArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the YARA rules CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--yara_rules PATH]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --yara_rules PATH, --yara-rules PATH',
      (u'                        Path to a file containing Yara rules '
       u'definitions.'),
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    yara_rules.YaraRulesArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  @shared_test_lib.skipUnlessHasTestFile([u'yara.rules'])
  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.yara_rules_path = self._GetTestFilePath([u'yara.rules'])

    test_tool = tools.CLITool()
    yara_rules.YaraRulesArgumentsHelper.ParseOptions(options, test_tool)

    self.assertIsNotNone(test_tool._yara_rules_string)

    with self.assertRaises(errors.BadConfigObject):
      yara_rules.YaraRulesArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
