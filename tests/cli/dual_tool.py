#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction tool object."""

import argparse
import unittest

from plaso.cli import dual_tool
from plaso.lib import errors

from tests.cli import test_lib


class DualToolTest(test_lib.CLIToolTestCase):
  """Tests for the dual tool object."""

  _EXPECTED_OUTPUT_STORAGE_FILE_OPTIONS = u'\n'.join([
      u'usage: dual_tool_test.py [--storage_file [STORAGE_FILE]]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --storage_file [STORAGE_FILE]',
      u'                        The path of the storage file.',
      u''])

  def testAddStorageFileOptions(self):
    """Tests the AddStorageFileOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'dual_tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = dual_tool.DualTool()
    test_tool.AddStorageFileOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_STORAGE_FILE_OPTIONS)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_tool = dual_tool.DualTool()

    options = test_lib.TestOptions()

    # ParseOptions will raise if source is not set.
    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options.source = self._GetTestFilePath([u'ímynd.dd'])

    test_tool.ParseOptions(options)

    # pylint: disable=protected-access
    self.assertRegexpMatches(test_tool._storage_file_path,
                             r'\d{14}-057741a6e98e9909e42c50bff59072b6.plaso')


if __name__ == '__main__':
  unittest.main()
