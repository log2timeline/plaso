#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the analysis tool object."""

import argparse
import unittest

from plaso.cli import analysis_tool
from plaso.cli import test_lib
from plaso.lib import errors


class StorageMediaToolTest(test_lib.CLIToolTestCase):
  """Tests for the analysis tool object."""

  _EXPECTED_OUTPUT_DEFAULT = u'\n'.join([
      u'usage: analysis_tool_test.py [-h]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  -h, --help  show this help message and exit',
      u''])

  _EXPECTED_OUTPUT_STORAGE_FILE_OPTIONS = u'\n'.join([
      u'usage: analysis_tool_test.py [-h] [STORAGE_FILE]',
      u'',
      u'Test argument parser.',
      u'',
      u'positional arguments:',
      u'  STORAGE_FILE  The path of the storage file.',
      u'',
      u'optional arguments:',
      u'  -h, --help    show this help message and exit',
      u''])

  def testAddStorageFileOptions(self):
    """Tests the AddStorageFileOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'analysis_tool_test.py',
        description=u'Test argument parser.')

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_OUTPUT_DEFAULT)

    test_tool = analysis_tool.AnalysisTool()
    test_tool.AddStorageFileOptions(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_OUTPUT_STORAGE_FILE_OPTIONS)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_tool = analysis_tool.AnalysisTool()

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options.storage_file = self._GetTestFilePath([u'psort_test.out'])

    test_tool.ParseOptions(options)

    # TODO: improve this test.


if __name__ == '__main__':
  unittest.main()
