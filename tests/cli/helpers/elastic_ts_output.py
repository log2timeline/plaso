#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Elastic Timesketch output module CLI arguments helper."""

import argparse
import unittest

from plaso.cli.helpers import elastic_ts_output
from plaso.lib import errors
from plaso.output import elastic_ts

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class ElasticTimesketchOutputArgumentsHelperTest(
    test_lib.OutputModuleArgumentsHelperTest):
  """Tests the Elastic Timesketch output module CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--timeline_id TIMELINE_ID] [--server HOSTNAME]
                     [--port PORT]

Test argument parser.

optional arguments:
  --port PORT           The port number of the server.
  --server HOSTNAME     The hostname or server IP address of the server.
  --timeline_id TIMELINE_ID, --timeline-id TIMELINE_ID
                        The ID of the Timesketch Timeline object this data is
                        tied to
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    elastic_ts_output.ElasticTimesketchOutputArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options._data_location = 'data'

    output_mediator = self._CreateOutputMediator()
    output_module = elastic_ts.ElasticTimesketchOutputModule(output_mediator)
    elastic_ts_output.ElasticTimesketchOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      elastic_ts_output.ElasticTimesketchOutputArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
