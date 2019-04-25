#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage file CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import storage_file
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class StorageFileArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the storage file CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [STORAGE_FILE]

Test argument parser.

positional arguments:
  STORAGE_FILE  Path to a storage file.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    storage_file.StorageFileArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_tool = tools.CLITool()

    options = cli_test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath(['test.plaso'])

    storage_file.StorageFileArgumentsHelper.ParseOptions(options, test_tool)
    self.assertEqual(test_tool._storage_file_path, options.storage_file)

    with self.assertRaises(errors.BadConfigObject):
      storage_file.StorageFileArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
