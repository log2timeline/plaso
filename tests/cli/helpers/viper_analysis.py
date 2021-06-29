#!/usr/bin/env python3
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

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--viper-hash HASH] [--viper-host HOST]
                     [--viper-port PORT] [--viper-protocol PROTOCOL]

Test argument parser.

{0:s}:
  --viper-hash HASH, --viper_hash HASH
                        Type of hash to use to query the Viper server, the
                        default is: sha256. Supported options: md5, sha256
  --viper-host HOST, --viper_host HOST
                        Hostname of the Viper server to query, the default is:
                        localhost
  --viper-port PORT, --viper_port PORT
                        Port of the Viper server to query, the default is:
                        8080.
  --viper-protocol PROTOCOL, --viper_protocol PROTOCOL
                        Protocol to use to query Viper, the default is: http.
                        Supported options: http, https
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
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
