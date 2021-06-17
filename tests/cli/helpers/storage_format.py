#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage format CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import storage_format
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class StorageFormatArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the storage format CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--storage_format FORMAT] [--task_storage_format FORMAT]

Test argument parser.

{0:s}:
  --storage_format FORMAT, --storage-format FORMAT
                        Format of the storage file, the default is: sqlite.
                        Supported options: sqlite
  --task_storage_format FORMAT, --task-storage-format FORMAT
                        Format for task storage, the default is: sqlite.
                        Supported options: redis, sqlite
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    storage_format.StorageFormatArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.storage_format = 'sqlite'
    options.task_storage_format = 'sqlite'

    test_tool = tools.CLITool()
    storage_format.StorageFormatArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._storage_format, options.storage_format)
    self.assertEqual(
        test_tool._task_storage_format, options.task_storage_format)

    with self.assertRaises(errors.BadConfigObject):
      storage_format.StorageFormatArgumentsHelper.ParseOptions(options, None)

    with self.assertRaises(errors.BadConfigOption):
      options.storage_format = 'bogus'
      storage_format.StorageFormatArgumentsHelper.ParseOptions(
          options, test_tool)


if __name__ == '__main__':
  unittest.main()
