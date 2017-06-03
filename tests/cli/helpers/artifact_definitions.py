#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the artifact definitions CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import artifact_definitions
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib


class ArtifactDefinitionsArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the artifact definitions CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--artifact_definitions PATH]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --artifact_definitions PATH, --artifact-definitions PATH',
      (u'                        Path to a directory containing artifact '
       u'definitions.'),
      (u'                        Artifact definitions can be used to '
       u'describe and'),
      (u'                        quickly collect data data of interest, '
       u'such as'),
      u'                        specific files or Windows Registry keys.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    artifact_definitions.ArtifactDefinitionsArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  @shared_test_lib.skipUnlessHasTestFile([u'artifacts'])
  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])

    test_tool = tools.CLITool()
    artifact_definitions.ArtifactDefinitionsArgumentsHelper.ParseOptions(
        options, test_tool)

    self.assertIsNotNone(test_tool._artifacts_registry)

    with self.assertRaises(errors.BadConfigObject):
      artifact_definitions.ArtifactDefinitionsArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
