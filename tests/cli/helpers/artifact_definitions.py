#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the artifact definitions CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import artifact_definitions
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class ArtifactDefinitionsArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the artifact definitions CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--artifact_definitions PATH]
                     [--custom_artifact_definitions PATH]

Test argument parser.

optional arguments:
  --artifact_definitions PATH, --artifact-definitions PATH
                        Path to a directory containing artifact definitions,
                        which are .yaml files. Artifact definitions can be
                        used to describe and quickly collect data of interest,
                        such as specific files or Windows Registry keys.
  --custom_artifact_definitions PATH, --custom-artifact-definitions PATH
                        Path to a file containing custom artifact definitions,
                        which are .yaml files. Artifact definitions can be
                        used to describe and quickly collect data of interest,
                        such as specific files or Windows Registry keys.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    artifact_definitions.ArtifactDefinitionsArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_file_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_file_path)

    test_tool = tools.CLITool()

    options = cli_test_lib.TestOptions()
    options.artifact_definitions_path = test_file_path

    artifact_definitions.ArtifactDefinitionsArgumentsHelper.ParseOptions(
        options, test_tool)
    self.assertIsNotNone(test_tool._artifact_definitions_path)

    with self.assertRaises(errors.BadConfigObject):
      artifact_definitions.ArtifactDefinitionsArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
