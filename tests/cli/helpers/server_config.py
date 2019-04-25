#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the server configuration CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli.helpers import server_config
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class MockOutputModule(object):
  """Mock output module for testing.

  Attributes:
    hostname (str): hostname or IP address of the database server.
    port (int): port number of the database server.
  """

  def __init__(self):
    """Initializes a mock output module."""
    super(MockOutputModule, self).__init__()
    self.hostname = None
    self.port = None

  def SetServerInformation(self, server, port):
    """Sets the server information.

    Args:
      server (str): hostname or IP address of the database server.
      port (int): port number of the database server.
    """
    self.hostname = server
    self.port = port


class ServerArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests the server configuration CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--server HOSTNAME] [--port PORT]

Test argument parser.

optional arguments:
  --port PORT        The port number of the server.
  --server HOSTNAME  The hostname or server IP address of the server.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    server_config.ServerArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    output_module = MockOutputModule()
    server_config.ServerArgumentsHelper.ParseOptions(options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      server_config.ServerArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
