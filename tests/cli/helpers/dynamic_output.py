#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dynamic output module CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli.helpers import dynamic_output
from plaso.lib import errors
from plaso.output import dynamic

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class DynamicOutputArgumentsHelperTest(
    test_lib.OutputModuleArgumentsHelperTest):
  """Tests the dynamic output module CLI arguments helper."""

  _EXPECTED_OUTPUT = '\n'.join([
      ('usage: cli_helper.py [--fields FIELDS] '
       '[--additional_fields ADDITIONAL_FIELDS]'),
      '', 'Test argument parser.', '', 'optional arguments:',
      '  --additional_fields ADDITIONAL_FIELDS',
      ('                        Defines extra fields to be included in the '
       'output, in'),
      ('                        addition to the default fields, which are '
       'datetime,'),
      ('                        timestamp_desc, source, source_long, message, '
       'parser,'),
      '                        display_name, tag.',
      ('  --fields FIELDS       Defines which fields should be included in the'
       ' output.'),
      ''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    dynamic_output.DynamicOutputArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    output_mediator = self._CreateOutputMediator()
    output_module = dynamic.DynamicOutputModule(output_mediator)
    dynamic_output.DynamicOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      dynamic_output.DynamicOutputArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
