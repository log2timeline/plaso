#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the status view CLI arguments helper."""

import argparse
import unittest

from plaso.cli import status_view as cli_status_view
from plaso.cli import tools
from plaso.cli.helpers import status_view
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class StatusViewArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the status view CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--status_view TYPE] [--status_view_file PATH]
                     [--status_view_interval SECONDS]

Test argument parser.

{0:s}:
  --status_view TYPE, --status-view TYPE
                        The processing status view mode: "file", "linear",
                        "none" or "window".
  --status_view_file PATH, --status-view-file PATH
                        The name of the status view file.
  --status_view_interval SECONDS, --status-view-interval SECONDS
                        Number of seconds to update the status view.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    status_view.StatusViewArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.status_view_mode = cli_status_view.StatusView.MODE_WINDOW
    options.status_view_interval = 0.5

    test_tool = tools.CLITool()
    status_view.StatusViewArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._status_view_mode, options.status_view_mode)

    with self.assertRaises(errors.BadConfigObject):
      status_view.StatusViewArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
