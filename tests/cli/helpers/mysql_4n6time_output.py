#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the 4n6time MySQL database output module CLI arguments helper."""

import argparse
import unittest

from plaso.cli.helpers import mysql_4n6time_output
from plaso.lib import errors
from plaso.output import mysql_4n6time

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class MySQL4n6TimeOutputArgumentsHelperTest(
    test_lib.OutputModuleArgumentsHelperTest):
  """Tests the 4n6time MySQL database output module CLI arguments helper."""

  _EXPECTED_OUTPUT = u'\n'.join([
      (u'usage: cli_helper.py [--append] [--evidence EVIDENCE] '
       u'[--fields FIELDS]'),
      (u'                     [--additional_fields ADDITIONAL_FIELDS] '
       u'[--user USERNAME]'),
      u'                     [--password PASSWORD] [--db_name DB_NAME]',
      u'                     [--server HOSTNAME] [--port PORT]',
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
      u'  --db_name DB_NAME, --db-name DB_NAME',
      u'                        The name of the database to connect to.',
      (u'  --evidence EVIDENCE   Set the evidence field to a specific value, '
       u'defaults'),
      u'                        to empty.',
      (u'  --fields FIELDS       Defines which fields should be indexed in '
       u'the'), u'                        database.',
      u'  --password PASSWORD   The password for the database user.',
      u'  --port PORT           The port number of the server.',
      (u'  --server HOSTNAME     The hostname or server IP address of the '
       u'server.'),
      u'  --user USERNAME       The username used to connect to the database.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    mysql_4n6time_output.MySQL4n6TimeOutputArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    output_mediator = self._CreateOutputMediator()
    output_module = mysql_4n6time.MySQL4n6TimeOutputModule(output_mediator)
    mysql_4n6time_output.MySQL4n6TimeOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      mysql_4n6time_output.MySQL4n6TimeOutputArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
