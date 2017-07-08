#!/usr/bin/python
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

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--storage_format FORMAT]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --storage_format FORMAT, --storage-format FORMAT',
      (u'                        Format of the storage file, the default '
       u'is: zip.'),
      u'                        Supported options: sqlite, zip',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    storage_format.StorageFormatArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.storage_format = u'sqlite'

    test_tool = tools.CLITool()
    storage_format.StorageFormatArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._storage_format, options.storage_format)

    with self.assertRaises(errors.BadConfigObject):
      storage_format.StorageFormatArgumentsHelper.ParseOptions(options, None)

    with self.assertRaises(errors.BadConfigOption):
      options.storage_format = u'bogus'
      storage_format.StorageFormatArgumentsHelper.ParseOptions(
          options, test_tool)


if __name__ == '__main__':
  unittest.main()
