#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the nsrlsvr analysis plugin CLI arguments helper."""

from __future__ import unicode_literals

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

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--nsrlsvr-hash HASH] [--nsrlsvr-host HOST]
                     [--nsrlsvr-label LABEL] [--nsrlsvr-port PORT]

Test argument parser.

optional arguments:
  --nsrlsvr-hash HASH, --nsrlsvr_hash HASH
                        Type of hash to use to query nsrlsvr instance, the
                        default is: md5. Supported options: md5, sha1
  --nsrlsvr-host HOST, --nsrlsvr_host HOST
                        Hostname or IP address of the nsrlsvr instance to
                        query, the default is: localhost
  --nsrlsvr-label LABEL, --nsrlsvr_label LABEL
                        Label to apply to events, the default is:
                        nsrl_present.
  --nsrlsvr-port PORT, --nsrlsvr_port PORT
                        Port number of the nsrlsvr instance to query, the
                        default is: 9120.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    nsrlsvr_analysis.NsrlsvrAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    analysis_plugin = nsrlsvr.NsrlsvrAnalysisPlugin()

    options.nsrlsvr_hash = 'sha1'
    options.nsrlsvr_host = '127.0.0.1'
    options.nsrlsvr_port = 9120
    options.nsrlsvr_label = 'NSRLSVR'

    with self.assertRaises(errors.BadConfigOption):
      nsrlsvr_analysis.NsrlsvrAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    self.assertEqual(analysis_plugin._analyzer._host, '127.0.0.1')
    self.assertEqual(analysis_plugin._analyzer._port, 9120)
    self.assertEqual(analysis_plugin._label, 'NSRLSVR')

    with self.assertRaises(errors.BadConfigObject):
      nsrlsvr_analysis.NsrlsvrAnalysisArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
