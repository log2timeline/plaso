#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the storage file CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import storage_file
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class StorageFileArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the storage file CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [STORAGE_FILE]',
      u'',
      u'Test argument parser.',
      u'',
      u'positional arguments:',
      u'  STORAGE_FILE  The path of the storage file.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    storage_file.StorageFileArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath([u'test.plaso'])

    test_tool = tools.CLITool()
    storage_file.StorageFileArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._storage_file_path, options.storage_file)

    with self.assertRaises(errors.BadConfigObject):
      storage_file.StorageFileArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
