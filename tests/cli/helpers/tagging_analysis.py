#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the tagging analysis plugin CLI arguments helper."""

from __future__ import unicode_literals

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

optional arguments:
  --tagging-file TAGGING_FILE, --tagging_file TAGGING_FILE
                        Specify a file to read tagging criteria from.
"""

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
    options = cli_test_lib.TestOptions()

    analysis_plugin = tagging.TaggingAnalysisPlugin()
    tagging_analysis.TaggingAnalysisArgumentsHelper.ParseOptions(
        options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      tagging_analysis.TaggingAnalysisArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
