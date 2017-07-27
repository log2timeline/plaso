#!/usr/bin/python
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

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--analysis PLUGIN_LIST]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --analysis PLUGIN_LIST',
      (u'                        A comma separated list of analysis plugin '
       u'names to be'),
      (u'                        loaded or "--analysis list" to see a list '
       u'of available'),
      u'                        plugins.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    analysis_plugins.AnalysisPluginsArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.analysis_plugins = u'tagging'

    test_tool = tools.CLITool()
    analysis_plugins.AnalysisPluginsArgumentsHelper.ParseOptions(
        options, test_tool)

    self.assertEqual(test_tool._analysis_plugins, [u'tagging'])

    with self.assertRaises(errors.BadConfigObject):
      analysis_plugins.AnalysisPluginsArgumentsHelper.ParseOptions(
          options, None)

    options.analysis_plugins = u'bogus'

    with self.assertRaises(errors.BadConfigOption):
      analysis_plugins.AnalysisPluginsArgumentsHelper.ParseOptions(
          options, test_tool)

    # TODO: add test for '--analysis list'
    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
