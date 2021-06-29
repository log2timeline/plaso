#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the filter file CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import artifact_filters
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class ArtifactFiltersArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the filter file CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--artifact_filters ARTIFACT_FILTERS]
                     [--artifact_filters_file PATH]

Test argument parser.

{0:s}:
  --artifact_filters ARTIFACT_FILTERS, --artifact-filters ARTIFACT_FILTERS
                        Names of forensic artifact definitions, provided on
                        the command command line (comma separated). Forensic
                        artifacts are stored in .yaml files that are directly
                        pulled from the artifact definitions project. You can
                        also specify a custom artifacts yaml file (see
                        --custom_artifact_definitions). Artifact definitions
                        can be used to describe and quickly collect data of
                        interest, such as specific files or Windows Registry
                        keys.
  --artifact_filters_file PATH, --artifact-filters_file PATH
                        Names of forensic artifact definitions, provided in a
                        file with one artifact name per line. Forensic
                        artifacts are stored in .yaml files that are directly
                        pulled from the artifact definitions project. You can
                        also specify a custom artifacts yaml file (see
                        --custom_artifact_definitions). Artifact definitions
                        can be used to describe and quickly collect data of
                        interest, such as specific files or Windows Registry
                        keys.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    artifact_filters.ArtifactFiltersArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.artifact_filter_string = 'TestFiles, TestFiles2'
    expected_output = ['TestFiles', 'TestFiles2']

    test_tool = tools.CLITool()
    artifact_filters.ArtifactFiltersArgumentsHelper.ParseOptions(
        options, test_tool)

    self.assertEqual(test_tool._artifact_filters, expected_output)

    options.artifact_filters_file = self._GetTestFilePath(
        ['artifacts', 'artifact_names'])

    with self.assertRaises(errors.BadConfigOption):
      artifact_filters.ArtifactFiltersArgumentsHelper.ParseOptions(
          options, test_tool)

    expected_output = ['TestFiles', 'TestFiles2', 'TestFiles3']

    options.artifact_filter_string = None
    artifact_filters.ArtifactFiltersArgumentsHelper.ParseOptions(
        options, test_tool)

    self.assertEqual(test_tool._artifact_filters, expected_output)

    options.file_filter = self._GetTestFilePath(['testdir', 'filter2.txt'])
    with self.assertRaises(errors.BadConfigOption):
      artifact_filters.ArtifactFiltersArgumentsHelper.ParseOptions(
          options, test_tool)

    with self.assertRaises(errors.BadConfigObject):
      artifact_filters.ArtifactFiltersArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
