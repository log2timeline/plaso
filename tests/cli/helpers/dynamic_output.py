#!/usr/bin/env python3
"""Tests for the dynamic output module CLI arguments helper."""

import unittest

from plaso.cli.helpers import dynamic_output
from plaso.lib import errors
from plaso.output import dynamic

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class DynamicOutputArgumentsHelperTest(
    test_lib.OutputModuleArgumentsHelperTest):
  """Tests the dynamic output module CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = f"""\
usage: cli_helper.py [--fields FIELDS]

Test argument parser.

{cli_test_lib.ARGPARSE_OPTIONS:s}:
  --fields FIELDS  Defines which fields should be included in the output.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = self._GetTestArgumentParser('cli_helper.py')

    dynamic_output.DynamicOutputArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    output_module = dynamic.DynamicOutputModule()
    dynamic_output.DynamicOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      dynamic_output.DynamicOutputArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
