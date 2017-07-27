#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dynamic output module CLI arguments helper."""

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

  _EXPECTED_OUTPUT = u'\n'.join([
      (u'usage: cli_helper.py [--fields FIELDS] '
       u'[--additional_fields ADDITIONAL_FIELDS]'),
      u'', u'Test argument parser.', u'', u'optional arguments:',
      u'  --additional_fields ADDITIONAL_FIELDS',
      (u'                        Defines extra fields to be included in the '
       u'output, in'),
      (u'                        addition to the default fields, which are '
       u'datetime,'),
      (u'                        timestamp_desc, source, source_long, message, '
       u'parser,'),
      u'                        display_name, tag.',
      (u'  --fields FIELDS       Defines which fields should be included in the'
       u' output.'),
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
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
