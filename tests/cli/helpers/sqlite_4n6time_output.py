#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the 4n6time SQLite database output module CLI arguments helper."""

import argparse
import unittest

from plaso.cli.helpers import sqlite_4n6time_output
from plaso.lib import errors
from plaso.output import sqlite_4n6time

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class SQLite4n6TimeOutputArgumentsHelperTEst(
    test_lib.OutputModuleArgumentsHelperTest):
  """Tests the 4n6time SQLite database output module CLI arguments helper."""

  _EXPECTED_OUTPUT = u'\n'.join([
      (u'usage: cli_helper.py [--append] [--evidence EVIDENCE] '
       u'[--fields FIELDS]'),
      u'                     [--additional_fields ADDITIONAL_FIELDS]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --additional_fields ADDITIONAL_FIELDS',
      (u'                        Defines extra fields to be included in the '
       u'output, in'),
      u'                        addition to the default fields, which are',
      u'                        datetime,host,source,sourcetype,user,type.',
      (u'  --append              Defines whether the intention is to append '
       u'to an'),
      (u'                        already existing database or overwrite it. '
       u'Defaults to'),
      u'                        overwrite.',
      (u'  --evidence EVIDENCE   Set the evidence field to a specific value, '
       u'defaults'),
      u'                        to empty.',
      (u'  --fields FIELDS       Defines which fields should be indexed in '
       u'the'), u'                        database.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    sqlite_4n6time_output.SQLite4n6TimeOutputArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    output_mediator = self._CreateOutputMediator()
    output_module = sqlite_4n6time.SQLite4n6TimeOutputModule(output_mediator)

    with self.assertRaises(errors.BadConfigOption):
      sqlite_4n6time_output.SQLite4n6TimeOutputArgumentsHelper.ParseOptions(
          options, output_module)

    options.write = u'4n6time.sqlite'
    sqlite_4n6time_output.SQLite4n6TimeOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      sqlite_4n6time_output.SQLite4n6TimeOutputArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
