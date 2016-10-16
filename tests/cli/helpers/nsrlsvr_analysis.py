#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the nsrlsvr analysis plugin CLI arguments helper."""

import argparse
import unittest

from plaso.analysis import nsrlsvr
from plaso.lib import errors
from plaso.cli.helpers import nsrlsvr_analysis

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class NsrlsvrAnalysisArgumentsHelperTest(
    test_lib.AnalysisPluginArgumentsHelperTest):
  """Tests the nsrlsvr analysis plugin CLI arguments helper."""

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--nsrlsvr-hash HASH] [--nsrlsvr-host HOST]',
      u'                     [--nsrlsvr-port PORT]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --nsrlsvr-hash HASH, --nsrlsvr_hash HASH',
      (u'                        Type of hash to use to query the NSRL server, '
       u'the'),
      u'                        default is: md5',
      u'  --nsrlsvr-host HOST, --nsrlsvr_host HOST',
      (u'                        Hostname of the NSRL server to query, '
       u'the default is:'),
      u'                        localhost',
      u'  --nsrlsvr-port PORT, --nsrlsvr_port PORT',
      (u'                        Port of the NSRL server to query, the '
       u'default is:'),
      u'                        9120.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    nsrlsvr_analysis.NsrlsvrAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    analysis_plugin = nsrlsvr.NsrlsvrAnalysisPlugin()
    with self.assertRaises(errors.BadConfigOption):
      nsrlsvr_analysis.NsrlsvrAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      nsrlsvr_analysis.NsrlsvrAnalysisArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
