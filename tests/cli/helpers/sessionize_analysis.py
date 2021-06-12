#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the sessionize analysis plugin CLI arguments helper."""

import argparse
import unittest

from plaso.analysis import sessionize
from plaso.cli.helpers import sessionize_analysis
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class SessionizeAnalysisArgumentsHelperTest(
    test_lib.AnalysisPluginArgumentsHelperTest):
  """Tests the sessionize analysis plugin CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--maximum-pause MINUTES]

Test argument parser.

{0:s}:
  --maximum-pause MINUTES, --maximum_pause MINUTES
                        Specify the maximum delay in minutes between events in
                        the session.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    sessionize_analysis.SessionizeAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    analysis_plugin = sessionize.SessionizeAnalysisPlugin()
    sessionize_analysis.SessionizeAnalysisArgumentsHelper.ParseOptions(
        options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      sessionize_analysis.SessionizeAnalysisArgumentsHelper.ParseOptions(
          options, None)

    options.sessionize_maximumpause = 0
    with self.assertRaises(errors.BadConfigOption):
      sessionize_analysis.SessionizeAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    options.sessionize_maximumpause = 'ten'
    with self.assertRaises(errors.BadConfigOption):
      sessionize_analysis.SessionizeAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)


if __name__ == '__main__':
  unittest.main()
