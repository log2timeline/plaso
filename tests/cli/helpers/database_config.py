#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the database configuration CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli.helpers import database_config
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class MockPartialOutputModule(object):
  """Mock of a partial output module for testing.

  Attributes:
    hostname (str): hostname or IP address of the database server.
    password (str): password to access the database.
    port (int): port number of the database server.
    username (str): username to access the database.
  """

  def __init__(self):
    """Initializes a partial mock output module."""
    super(MockPartialOutputModule, self).__init__()
    self.hostname = None
    self.password = None
    self.port = None
    self.username = None

  def SetCredentials(self, password=None, username=None):
    """Sets the database credentials.

    Args:
      password (Optional[str]): password to access the database.
      username (Optional[str]): username to access the database.
    """
    self.password = password
    self.username = username

  def SetServerInformation(self, server, port):
    """Sets the server information.

    Args:
      server (str): hostname or IP address of the database server.
      port (int): port number of the database server.
    """
    self.hostname = server
    self.port = port


class MockOutputModule(MockPartialOutputModule):
  """Mock output module for testing.

  Attributes:
    database_name (str): name of the database.
  """

  def __init__(self):
    """Initializes a mock output module."""
    super(MockOutputModule, self).__init__()
    self.database_name = None

  def SetDatabaseName(self, name):
    """Sets the database name.

    Args:
      name (str): name of the database.
    """
    self.database_name = name


class DatabaseArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests the database configuration CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--user USERNAME] [--password PASSWORD]
                     [--db_name DB_NAME] [--server HOSTNAME] [--port PORT]

Test argument parser.

optional arguments:
  --db_name DB_NAME, --db-name DB_NAME
                        The name of the database to connect to.
  --password PASSWORD   The password for the database user.
  --port PORT           The port number of the server.
  --server HOSTNAME     The hostname or server IP address of the server.
  --user USERNAME       The username used to connect to the database.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    database_config.DatabaseArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    output_module = MockOutputModule()
    database_config.DatabaseArgumentsHelper.ParseOptions(options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      database_config.DatabaseArgumentsHelper.ParseOptions(options, None)

    output_module = MockPartialOutputModule()
    with self.assertRaises(errors.BadConfigObject):
      database_config.DatabaseArgumentsHelper.ParseOptions(
          options, output_module)


if __name__ == '__main__':
  unittest.main()
