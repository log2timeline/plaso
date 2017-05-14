#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction tool object."""

import argparse
import unittest

from plaso.cli import extract_analyze_tool
from plaso.lib import errors

from tests.cli import test_lib


class ExtractionAndAnalysisToolTest(test_lib.CLIToolTestCase):
  """Tests for the extraction and analysis tool object."""

  _STORAGE_FILENAME_TEMPLATE = ur'\d{{8}}T\d{{6}}-{filename}.plaso'

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT_STORAGE_FILE_OPTIONS = u'\n'.join([
      u'usage: extract_analyze_tool_test.py [--storage_file [STORAGE_FILE]]',
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
        prog=u'extract_analyze_tool_test.py',
        description=u'Test argument parser.',
        add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = extract_analyze_tool.ExtractionAndAnalysisTool()
    test_tool.AddStorageFileOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_STORAGE_FILE_OPTIONS)

  def testGenerateStorageFileName(self):
    """Tests the _GenerateStorageFileName function."""
    test_tool = extract_analyze_tool.ExtractionAndAnalysisTool()

    test_tool._source_path = u'/test/storage/path'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename=u'path')
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

    test_tool._source_path = u'/test/storage/path/'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename=u'path')
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

    test_tool._source_path = u'/'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename=u'ROOT')
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

    test_tool._source_path = u'/foo/..'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename=u'ROOT')
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

    test_tool._source_path = u'foo/../bar'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename=u'bar')
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_tool = extract_analyze_tool.ExtractionAndAnalysisTool()

    options = test_lib.TestOptions()

    # ParseOptions will raise if source is not set.
    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options.source = self._GetTestFilePath([u'ímynd.dd'])

    test_tool.ParseOptions(options)
    storage_path_regex = self._STORAGE_FILENAME_TEMPLATE.format(
        filename=u'ímynd.dd')
    self.assertRegexpMatches(test_tool._storage_file_path, storage_path_regex)


if __name__ == '__main__':
  unittest.main()
