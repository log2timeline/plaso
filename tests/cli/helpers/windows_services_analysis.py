#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Services analysis plugin CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.analysis import windows_services
from plaso.lib import errors
from plaso.cli.helpers import windows_services_analysis as arguments_helper

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class WindowsServicesAnalysisArgumentsHelperTest(
    test_lib.AnalysisPluginArgumentsHelperTest):
  """Tests the Windows Services analysis plugin CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--windows-services-output {text,yaml}]

Test argument parser.

optional arguments:
  --windows-services-output {text,yaml}
                        Specify how the results should be displayed. Options
                        are text and yaml.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    arguments_helper.WindowsServicesAnalysisArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    analysis_plugin = windows_services.WindowsServicesAnalysisPlugin()
    arguments_helper.WindowsServicesAnalysisArgumentsHelper.ParseOptions(
        options, analysis_plugin)

    with self.assertRaises(errors.BadConfigObject):
      arguments_helper.WindowsServicesAnalysisArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
