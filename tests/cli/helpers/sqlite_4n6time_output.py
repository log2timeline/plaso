#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the 4n6time SQLite database output module CLI arguments helper."""

from __future__ import unicode_literals

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

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--append] [--evidence EVIDENCE] [--fields FIELDS]
                     [--additional_fields ADDITIONAL_FIELDS]

Test argument parser.

optional arguments:
  --additional_fields ADDITIONAL_FIELDS
                        Defines extra fields to be included in the output, in
                        addition to the default fields, which are
                        datetime,host,source,sourcetype,user,type.
  --append              Defines whether the intention is to append to an
                        already existing database or overwrite it. Defaults to
                        overwrite.
  --evidence EVIDENCE   Set the evidence field to a specific value, defaults
                        to empty.
  --fields FIELDS       Defines which fields should be indexed in the
                        database.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
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

    options.write = '4n6time.sqlite'
    sqlite_4n6time_output.SQLite4n6TimeOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      sqlite_4n6time_output.SQLite4n6TimeOutputArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
