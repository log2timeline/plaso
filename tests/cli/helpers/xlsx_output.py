#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the XLSX output module CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli.helpers import xlsx_output
from plaso.lib import errors
from plaso.output import xlsx

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class XLSXOutputArgumentsHelperTest(test_lib.OutputModuleArgumentsHelperTest):
  """Tests the XLSX output module CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--fields FIELDS] [--additional_fields ADDITIONAL_FIELDS]
                     [--timestamp_format TIMESTAMP_FORMAT]

Test argument parser.

optional arguments:
  --additional_fields ADDITIONAL_FIELDS
                        Defines extra fields to be included in the output, in
                        addition to the default fields, which are datetime,tim
                        estamp_desc,source,source_long,message,parser,display_
                        name,tag.
  --fields FIELDS       Defines which fields should be included in the output.
  --timestamp_format TIMESTAMP_FORMAT
                        Set the timestamp format that will be used in the
                        datetimecolumn of the XLSX spreadsheet.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
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

    options.write = 'plaso.xlsx'
    xlsx_output.XLSXOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      xlsx_output.XLSXOutputArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
