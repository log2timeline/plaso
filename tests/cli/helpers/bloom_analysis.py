#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bloom database analysis plugin CLI arguments helper."""

import argparse
import unittest

try:
  import flor
  from plaso.analysis import bloom
  from plaso.cli.helpers import bloom_analysis
except ModuleNotFoundError:
  flor = None

from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


@unittest.skipIf(flor is None, 'missing flor support')
class BloomAnalysisArgumentsHelperTest(
    test_lib.AnalysisPluginArgumentsHelperTest):
  """Tests the bloom database analysis plugin CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--bloom-file PATH] [--bloom-hash HASH]
                     [--bloom-label LABEL]

Test argument parser.

{0:s}:
  --bloom-file PATH, --bloom_file PATH
                        Path to the bloom database file, the default is:
                        hashlookup-full.bloom
  --bloom-hash HASH, --bloom_hash HASH
                        Type of hash to use to query the bloom database file
                        (note that hash values must be stored in upper case),
                        the default is: sha1. Supported options: md5, sha1,
                        sha256.
  --bloom-label LABEL, --bloom_label LABEL
                        Label to apply to events, the default is:
                        bloom_present.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    bloom_analysis.BloomAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    analysis_plugin = bloom.BloomAnalysisPlugin()

    with self.assertRaises(errors.BadConfigOption):
      bloom_analysis.BloomAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      bloom_analysis.BloomAnalysisArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
