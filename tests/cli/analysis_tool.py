#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the analysis tool object."""

import argparse
import unittest

from plaso.cli import analysis_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class StorageMediaToolTest(test_lib.CLIToolTestCase):
  """Tests for the analysis tool object."""

  _EXPECTED_OUTPUT_STORAGE_FILE_OPTIONS = u'\n'.join([
      u'usage: analysis_tool_test.py [STORAGE_FILE]',
      u'',
      u'Test argument parser.',
      u'',
      u'positional arguments:',
      u'  STORAGE_FILE  The path of the storage file.',
      u''])

  def testAddStorageFileOptions(self):
    """Tests the AddStorageFileOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'analysis_tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = analysis_tool.AnalysisTool()
    test_tool.AddStorageFileOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_STORAGE_FILE_OPTIONS)

  @shared_test_lib.skipUnlessHasTestFile([u'psort_test.json.plaso'])
  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_tool = analysis_tool.AnalysisTool()

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options.storage_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    test_tool.ParseOptions(options)

    # TODO: improve this test.


if __name__ == '__main__':
  unittest.main()
