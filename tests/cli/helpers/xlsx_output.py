#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the XLSX output module CLI arguments helper."""

import argparse
import unittest

from plaso.cli.helpers import xlsx_output
from plaso.lib import errors
from plaso.output import xlsx

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class XLSXOutputArgumentsHelperTest(test_lib.OutputModuleArgumentsHelperTest):
  """Tests the XLSX output module CLI arguments helper."""

  _EXPECTED_OUTPUT = u'\n'.join([
      (u'usage: cli_helper.py [--fields FIELDS] '
       u'[--additional_fields ADDITIONAL_FIELDS]'),
      u'                     [--timestamp_format TIMESTAMP_FORMAT]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --additional_fields ADDITIONAL_FIELDS',
      (u'                        Defines extra fields to be included in the '
       u'output, in'),
      (u'                        addition to the default fields, which are '
       u'datetime,tim'),
      (u'                        estamp_desc,source,source_long,message,parser,'
       u'display_'), u'                        name,tag.',
      (u'  --fields FIELDS       Defines which fields should be included in '
       u'the output.'),
      u'  --timestamp_format TIMESTAMP_FORMAT',
      (u'                        Set the timestamp format that will be used '
       u'in the'),
      u'                        datetimecolumn of the XLSX spreadsheet.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    xlsx_output.XLSXOutputArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    output_mediator = self._CreateOutputMediator()
    output_module = xlsx.XLSXOutputModule(output_mediator)

    with self.assertRaises(errors.BadConfigOption):
      xlsx_output.XLSXOutputArgumentsHelper.ParseOptions(
          options, output_module)

    options.write = u'plaso.xlsx'
    xlsx_output.XLSXOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      xlsx_output.XLSXOutputArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
