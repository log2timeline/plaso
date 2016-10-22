#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Viper analysis plugin CLI arguments helper."""

import argparse
import unittest

from plaso.analysis import viper
from plaso.lib import errors
from plaso.cli.helpers import viper_analysis

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class ViperAnalysisArgumentsHelperTest(
    test_lib.AnalysisPluginArgumentsHelperTest):
  """Tests the Viper analysis plugin CLI arguments helper."""

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--viper-hash HASH] [--viper-host HOST]',
      u'                     [--viper-port PORT] [--viper-protocol PROTOCOL]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --viper-hash HASH, --viper_hash HASH',
      (u'                        Type of hash to use to query the Viper '
       u'server, the'),
      (u'                        default is: sha256. Supported options: md5, '
       u'sha256'),
      u'  --viper-host HOST, --viper_host HOST',
      (u'                        Hostname of the Viper server to query, the '
       u'default is:'),
      u'                        localhost',
      u'  --viper-port PORT, --viper_port PORT',
      (u'                        Port of the Viper server to query, the '
       u'default is:'),
      u'                        8080.',
      u'  --viper-protocol PROTOCOL, --viper_protocol PROTOCOL',
      (u'                        Protocol to use to query Viper, the '
       u'default is: http.'),
      u'                        Supported options: http, https',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    viper_analysis.ViperAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    analysis_plugin = viper.ViperAnalysisPlugin()

    with self.assertRaises(errors.BadConfigOption):
      viper_analysis.ViperAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      viper_analysis.ViperAnalysisArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
