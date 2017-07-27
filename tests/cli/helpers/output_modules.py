#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the output modules CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import output_modules
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class OutputModulesArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the output modules CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [-o FORMAT] [-w OUTPUT_FILE] [--fields FIELDS]',
      u'                     [--additional_fields ADDITIONAL_FIELDS]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --additional_fields ADDITIONAL_FIELDS',
      (u'                        Defines extra fields to be included in the '
       u'output, in'),
      (u'                        addition to the default fields, which are '
       u'datetime,'),
      (u'                        timestamp_desc, source, source_long, message, '
       u'parser,'),
      u'                        display_name, tag.',
      (u'  --fields FIELDS       Defines which fields should be included in '
       u'the output.'),
      u'  -o FORMAT, --output_format FORMAT, --output-format FORMAT',
      (u'                        The output format. Use "-o list" to see a '
       u'list of'),
      u'                        available output formats.',
      u'  -w OUTPUT_FILE, --write OUTPUT_FILE',
      u'                        Output filename.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    output_modules.OutputModulesArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.output_format = u'dynamic'
    options.write = u'output.dynamic'

    test_tool = tools.CLITool()

    output_modules.OutputModulesArgumentsHelper.ParseOptions(
        options, test_tool)

    self.assertEqual(test_tool._output_format, options.output_format)
    self.assertEqual(test_tool._output_filename, options.write)

    # Test with a configuation object missing.
    with self.assertRaises(errors.BadConfigObject):
      output_modules.OutputModulesArgumentsHelper.ParseOptions(options, None)

    # Test with output format missing.
    options = cli_test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      output_modules.OutputModulesArgumentsHelper.ParseOptions(
          options, test_tool)

    # Test with output file missing.
    options.output_format = u'dynamic'

    with self.assertRaises(errors.BadConfigOption):
      output_modules.OutputModulesArgumentsHelper.ParseOptions(
          options, test_tool)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
