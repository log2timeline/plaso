#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output modules CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import output_modules
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class OutputModulesArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the output modules CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [-o FORMAT] [-w OUTPUT_FILE] [--fields FIELDS]
                     [--additional_fields ADDITIONAL_FIELDS]

Test argument parser.

optional arguments:
  --additional_fields ADDITIONAL_FIELDS
                        Defines extra fields to be included in the output, in
                        addition to the default fields, which are datetime,
                        timestamp_desc, source, source_long, message, parser,
                        display_name, tag.
  --fields FIELDS       Defines which fields should be included in the output.
  -o FORMAT, --output_format FORMAT, --output-format FORMAT
                        The output format. Use "-o list" to see a list of
                        available output formats.
  -w OUTPUT_FILE, --write OUTPUT_FILE
                        Output filename.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    output_modules.OutputModulesArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.output_format = 'dynamic'
    options.write = 'output.dynamic'

    test_tool = tools.CLITool()

    output_modules.OutputModulesArgumentsHelper.ParseOptions(
        options, test_tool)

    self.assertEqual(test_tool._output_format, options.output_format)
    self.assertEqual(test_tool._output_filename, options.write)

    # Test with a configuration object missing.
    with self.assertRaises(errors.BadConfigObject):
      output_modules.OutputModulesArgumentsHelper.ParseOptions(options, None)

    # Test with output format missing.
    options = cli_test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      output_modules.OutputModulesArgumentsHelper.ParseOptions(
          options, test_tool)

    # Test with output file missing.
    options.output_format = 'dynamic'

    with self.assertRaises(errors.BadConfigOption):
      output_modules.OutputModulesArgumentsHelper.ParseOptions(
          options, test_tool)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
