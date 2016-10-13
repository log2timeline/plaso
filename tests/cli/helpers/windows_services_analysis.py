#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Services analysis plugin CLI arguments helper."""

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

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--windows-services-output {text,yaml}]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --windows-services-output {text,yaml}',
      (u'                        Specify how the results should be displayed. '
       u'Options'),
      u'                        are text and yaml.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
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
