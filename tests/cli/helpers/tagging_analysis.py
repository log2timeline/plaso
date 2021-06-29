#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tagging analysis plugin CLI arguments helper."""

import argparse
import unittest

from plaso.analysis import tagging
from plaso.lib import errors
from plaso.cli.helpers import tagging_analysis

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class TaggingAnalysisArgumentsHelperTest(
    test_lib.AnalysisPluginArgumentsHelperTest):
  """Tests the tagging analysis plugin CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--tagging-file TAGGING_FILE]

Test argument parser.

{0:s}:
  --tagging-file TAGGING_FILE, --tagging_file TAGGING_FILE
                        Specify a file to read tagging criteria from.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    tagging_analysis.TaggingAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_file_path = self._GetTestFilePath(['tagging_file', 'valid.txt'])
    self._SkipIfPathNotExists(test_file_path)

    options = cli_test_lib.TestOptions()
    options.tagging_file = test_file_path

    analysis_plugin = tagging.TaggingAnalysisPlugin()
    tagging_analysis.TaggingAnalysisArgumentsHelper.ParseOptions(
        options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      tagging_analysis.TaggingAnalysisArgumentsHelper.ParseOptions(
          options, None)

    options.tagging_file = None

    with self.assertRaises(errors.BadConfigOption):
      tagging_analysis.TaggingAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    test_file_path = self._GetTestFilePath([
        'tagging_file', 'invalid_syntax.txt'])
    self._SkipIfPathNotExists(test_file_path)

    options.tagging_file = test_file_path

    with self.assertRaises(errors.BadConfigOption):
      tagging_analysis.TaggingAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)

    options.tagging_file = self._GetTestFilePath([
        'tagging_file', 'invalid_encoding.txt'])

    with self.assertRaises(errors.BadConfigOption):
      tagging_analysis.TaggingAnalysisArgumentsHelper.ParseOptions(
          options, analysis_plugin)


if __name__ == '__main__':
  unittest.main()
