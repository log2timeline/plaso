#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the VirusTotal analysis plugin CLI arguments helper."""

import argparse
import unittest

from plaso.analysis import virustotal
from plaso.lib import errors
from plaso.cli.helpers import virustotal_analysis

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class VirusTotalAnalysisArgumentsHelperTest(
    test_lib.AnalysisPluginArgumentsHelperTest):
  """Tests the VirusTotal analysis plugin CLI arguments helper."""

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--virustotal-api-key API_KEY]',
      (u'                     [--virustotal-free-rate-limit] '
       u'[--virustotal-hash HASH]'),
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --virustotal-api-key API_KEY, --virustotal_api_key API_KEY',
      u'                        Specify the API key for use with VirusTotal.',
      u'  --virustotal-free-rate-limit, --virustotal_free_rate_limit',
      (u'                        Limit Virustotal requests to the default '
       u'free API key'),
      (u'                        rate of 4 requests per minute. Set this to '
       u'false if'),
      u'                        you have an key for the private API.',
      u'  --virustotal-hash HASH, --virustotal_hash HASH',
      (u'                        Type of hash to query VirusTotal, the '
       u'default is:'),
      u'                        sha256',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    virustotal_analysis.VirusTotalAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    analysis_plugin = virustotal.VirusTotalAnalysisPlugin()

    with self.assertRaises(errors.BadConfigOption):
      virustotal_analysis.VirusTotalAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    options.virustotal_api_key = u'TEST'
    virustotal_analysis.VirusTotalAnalysisArgumentsHelper.ParseOptions(
        options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      virustotal_analysis.VirusTotalAnalysisArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
