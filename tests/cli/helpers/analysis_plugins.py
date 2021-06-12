#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the analysis plugins CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import analysis_plugins
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class AnalysisPluginsArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the analysis plugins CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--analysis PLUGIN_LIST]

Test argument parser.

{0:s}:
  --analysis PLUGIN_LIST
                        A comma separated list of analysis plugin names to be
                        loaded or "--analysis list" to see a list of available
                        plugins.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    analysis_plugins.AnalysisPluginsArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.analysis_plugins = 'tagging'

    test_tool = tools.CLITool()
    analysis_plugins.AnalysisPluginsArgumentsHelper.ParseOptions(
        options, test_tool)

    self.assertEqual(test_tool._analysis_plugins, ['tagging'])

    with self.assertRaises(errors.BadConfigObject):
      analysis_plugins.AnalysisPluginsArgumentsHelper.ParseOptions(
          options, None)

    options.analysis_plugins = 'bogus'

    with self.assertRaises(errors.BadConfigOption):
      analysis_plugins.AnalysisPluginsArgumentsHelper.ParseOptions(
          options, test_tool)

    # TODO: add test for '--analysis list'
    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
