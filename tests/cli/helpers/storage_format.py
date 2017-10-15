#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the storage format CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import storage_format
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class StorageFormatArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the storage format CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = '\n'.join([
      'usage: cli_helper.py [--storage_format FORMAT]',
      '',
      'Test argument parser.',
      '',
      'optional arguments:',
      '  --storage_format FORMAT, --storage-format FORMAT',
      ('                        Format of the storage file, the default '
       'is: zip.'),
      '                        Supported options: sqlite, zip',
      ''])

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

    test_tool = tools.CLITool()
    storage_format.StorageFormatArgumentsHelper.ParseOptions(options, test_tool)

    # pylint: disable=no-member
    self.assertEqual(test_tool._storage_format, options.storage_format)

    with self.assertRaises(errors.BadConfigObject):
      storage_format.StorageFormatArgumentsHelper.ParseOptions(options, None)

    with self.assertRaises(errors.BadConfigOption):
      options.storage_format = 'bogus'
      storage_format.StorageFormatArgumentsHelper.ParseOptions(
          options, test_tool)


if __name__ == '__main__':
  unittest.main()
