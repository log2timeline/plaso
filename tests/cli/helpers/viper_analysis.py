#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Viper analysis plugin CLI arguments helper."""

import argparse
import unittest

from plaso.lib import errors

from plaso.analysis import viper
from plaso.cli.helpers import viper_analysis

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class ViperAnalysisArgumentsHelperTest(
    test_lib.AnalysisPluginArgumentsHelperTest):
  """Tests the Viper analysis plugin CLI arguments helper."""

  _EXPECTED_OUTPUT = u'\n'.join([
      (u'usage: cli_helper.py [--viper-host VIPER_HOST] '
       u'[--viper-protocol {http,https}]'),
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --viper-host VIPER_HOST',
      u'                        Specify the host to query Viper on.',
      u'  --viper-protocol {http,https}',
      u'                        Protocol to use to query Viper.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    viper_analysis.ViperAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    analysis_plugin = viper.ViperAnalysisPlugin()
    viper_analysis.ViperAnalysisArgumentsHelper.ParseOptions(
        options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      viper_analysis.ViperAnalysisArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
