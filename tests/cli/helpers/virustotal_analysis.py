#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the VirusTotal analysis plugin CLI arguments helper."""

import argparse
import unittest

from plaso.analysis import virustotal
from plaso.lib import errors
from plaso.cli.helpers import virustotal_analysis

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class TestVirusTotalAnalysisPlugin(virustotal.VirusTotalAnalysisPlugin):
  """VirusTotal analysis plugin for testing."""

  def TestConnection(self):
    """Tests the connection to VirusTotal

    Returns:
      bool: True if VirusTotal is reachable.
    """
    return False


class VirusTotalAnalysisArgumentsHelperTest(
    test_lib.AnalysisPluginArgumentsHelperTest):
  """Tests the VirusTotal analysis plugin CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--virustotal-api-key API_KEY]
                     [--virustotal-free-rate-limit] [--virustotal-hash HASH]

Test argument parser.

{0:s}:
  --virustotal-api-key API_KEY, --virustotal_api_key API_KEY
                        Specify the API key for use with VirusTotal.
  --virustotal-free-rate-limit, --virustotal_free_rate_limit
                        Limit Virustotal requests to the default free API key
                        rate of 4 requests per minute. Set this to false if
                        you have an key for the private API.
  --virustotal-hash HASH, --virustotal_hash HASH
                        Type of hash to query VirusTotal, the default is:
                        sha256
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    virustotal_analysis.VirusTotalAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    # A test version of the VirusTotal analysis plugin is used to simulate
    # a connectivity failure.
    analysis_plugin = TestVirusTotalAnalysisPlugin()

    with self.assertRaises(errors.BadConfigOption):
      virustotal_analysis.VirusTotalAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    options.virustotal_api_key = 'TEST'
    with self.assertRaises(errors.BadConfigOption):
      virustotal_analysis.VirusTotalAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      virustotal_analysis.VirusTotalAnalysisArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
