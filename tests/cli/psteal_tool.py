#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the psteal CLI tool."""

from __future__ import unicode_literals

import io
import os
import unittest

from dfvfs.resolver import resolver as dfvfs_resolver

from plaso.cli import psteal_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class PstealToolTest(test_lib.CLIToolTestCase):
  """Tests for the psteal CLI tool."""

  # pylint: disable=protected-access

  _BDE_PASSWORD = 'bde-TEST'

  _EXPECTED_PROCESSING_OPTIONS = '\n'.join([
      'usage: psteal_test.py',
      '',
      'Test argument parser.',
      ''])

  _STORAGE_FILENAME_TEMPLATE = r'\d{{8}}T\d{{6}}-{filename}.plaso'

  def _CheckOutput(self, output, expected_output):
    """Compares the output against the expected output.

    The actual processing time is ignored, since it can vary.

    Args:
      output (str): tool output.
      expected_output (list[str]): expected tool output.
    """
    output = output.split('\n')

    self.assertEqual(output[:3], expected_output[:3])
    self.assertTrue(output[3].startswith('Processing time\t\t: '))
    self.assertEqual(output[4:], expected_output[4:])

  def testGenerateStorageFileName(self):
    """Tests the _GenerateStorageFileName function."""
    test_tool = psteal_tool.PstealTool()

    test_tool._source_path = '/test/storage/path'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='path')
    # pylint: disable=deprecated-method
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

    test_tool._source_path = '/test/storage/path/'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='path')
    # pylint: disable=deprecated-method
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

    test_tool._source_path = '/'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='ROOT')
    # pylint: disable=deprecated-method
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

    test_tool._source_path = '/foo/..'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='ROOT')
    # pylint: disable=deprecated-method
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

    test_tool._source_path = 'foo/../bar'
    storage_filename = test_tool._GenerateStorageFileName()
    expected_storage_filename = self._STORAGE_FILENAME_TEMPLATE.format(
        filename='bar')
    # pylint: disable=deprecated-method
    self.assertRegexpMatches(storage_filename, expected_storage_filename)

  def testFailWhenOutputAlreadyExists(self):
    """Test to make sure the tool raises when the output file already exists."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.storage_file = test_file_path
    options.source = 'unused_source'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.log_file = os.path.join(temp_directory, 'output.log')
      options.write = os.path.join(temp_directory, 'output.txt')

      with open(options.write, 'w') as file_object:
        file_object.write('bogus')

      # Test when output file already exists.
      # Escape \ otherwise assertRaisesRegexp can error with:
      # error: bogus escape: '\\1'
      expected_error = 'Output file already exists: {0:s}.'.format(
          options.write.replace('\\', '\\\\'))
      # pylint: disable=deprecated-method
      with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
        test_tool.ParseOptions(options)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['testdir'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.source = 'source'
    # Test when the output file is missing.
    expected_error = 'Output format: dynamic requires an output file'
    # pylint: disable=deprecated-method
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

    options = test_lib.TestOptions()
    options.write = 'output.csv'
    # Test when the source is missing.
    expected_error = 'Missing source path.'

    # pylint: disable=deprecated-method
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

    # Test when the source is missing.
    expected_error = 'Missing source path.'
    # pylint: disable=deprecated-method
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.log_file = os.path.join(temp_directory, 'output.log')
      options.source = test_file_path
      options.write = os.path.join(temp_directory, 'dynamic.out')

      # Test when both source and output are specified.
      test_tool.ParseOptions(options)

      with open(options.write, 'w') as file_object:
        file_object.write('bogus')

      # Test when output file already exists.
      # Escape \ otherwise assertRaisesRegexp can error with:
      # error: bogus escape: '\\1'
      expected_error = 'Output file already exists: {0:s}.'.format(
          options.write.replace('\\', '\\\\'))
      # pylint: disable=deprecated-method
      with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
        test_tool.ParseOptions(options)

  def testParseArguments(self):
    """Tests the ParseArguments function"""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    # Test ParseArguments with no output file nor source.
    result = test_tool.ParseArguments([])
    self.assertFalse(result)
    output = output_writer.ReadOutput()
    expected_error = 'ERROR: Output format: dynamic requires an output file'
    self.assertIn(expected_error, output)

  def testExtractEventsFromSourceDirectory(self):
    """Tests the ExtractEventsFromSources function on a directory."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['testdir'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.quiet = True
    options.status_view_mode = 'none'
    options.source = test_file_path

    with shared_test_lib.TempDirectory() as temp_directory:
      options.log_file = os.path.join(temp_directory, 'output.log')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.write = os.path.join(temp_directory, 'output.txt')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: directory',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  # TODO: Fix test https://github.com/log2timeline/plaso/issues/2253.
  @unittest.skip('failing on Windows')
  def testExtractEventsFromSourceBDEImage(self):
    """Tests the ExtractEventsFromSources function on an image with BDE."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['bdetogo.raw'])
    self._SkipIfPathNotExists(test_file_path)

    dfvfs_resolver.Resolver.key_chain.Empty()

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.credentials = ['password:{0:s}'.format(self._BDE_PASSWORD)]
    options.quiet = True
    options.source = test_file_path
    options.status_view_mode = 'none'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.log_file = os.path.join(temp_directory, 'output.log')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.write = os.path.join(temp_directory, 'output.txt')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: storage media image',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourcesImage(self):
    """Tests the ExtractEventsFromSources function on a single partition."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.quiet = True
    options.status_view_mode = 'none'
    options.source = test_file_path

    with shared_test_lib.TempDirectory() as temp_directory:
      options.log_file = os.path.join(temp_directory, 'output.log')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.write = os.path.join(temp_directory, 'output.txt')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: storage media image',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourcePartitionedImage(self):
    """Tests the ExtractEventsFromSources function on a partitioned image."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    # Note that the source file is a RAW (VMDK flat) image.
    test_file_path = self._GetTestFilePath(['multi_partition_image.vmdk'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.partitions = 'all'
    options.quiet = True
    options.status_view_mode = 'none'
    options.source = test_file_path

    with shared_test_lib.TempDirectory() as temp_directory:
      options.log_file = os.path.join(temp_directory, 'output.log')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.write = os.path.join(temp_directory, 'output.txt')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: storage media image',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourceVSSImage(self):
    """Tests the ExtractEventsFromSources function on an image with VSS."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.quiet = True
    options.single_process = True
    options.status_view_mode = 'none'
    options.source = test_file_path
    options.vss_stores = 'all'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.log_file = os.path.join(temp_directory, 'output.log')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.write = os.path.join(temp_directory, 'output.txt')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: storage media image',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          'Number of warnings generated while extracting events: 3.',
          '',
          'Use pinfo to inspect warnings in more detail.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testExtractEventsFromSourceSingleFile(self):
    """Tests the ExtractEventsFromSources function on a single file."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['System.evtx'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.quiet = True
    options.status_view_mode = 'none'
    options.source = test_file_path

    with shared_test_lib.TempDirectory() as temp_directory:
      options.log_file = os.path.join(temp_directory, 'output.log')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')
      options.write = os.path.join(temp_directory, 'output.txt')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          '',
          'Source path\t\t: {0:s}'.format(options.source),
          'Source type\t\t: single file',
          'Processing time\t\t: 00:00:00',
          '',
          'Processing started.',
          'Processing completed.',
          '',
          '']

      output = output_writer.ReadOutput()
      self._CheckOutput(output, expected_output)

  def testProcessStorage(self):
    """Test the AnalyzeEvents function"""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    expected_output_file_path = self._GetTestFilePath(
        ['end_to_end', 'dynamic.log'])
    self._SkipIfPathNotExists(expected_output_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.storage_file = test_file_path
    options.source = 'unused_source'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.log_file = os.path.join(temp_directory, 'output.log')
      options.write = os.path.join(temp_directory, 'output.txt')

      test_tool.ParseOptions(options)
      test_tool.AnalyzeEvents()

      with io.open(
          expected_output_file_path, 'rt', encoding='utf-8') as file_object:
        expected_output = file_object.read()

      with io.open(options.write, 'rt', encoding='utf-8') as file_object:
        result_output = file_object.read()

      expected_output = sorted(expected_output.split('\n'))
      result_output = sorted(result_output.split('\n'))
      self.assertEqual(expected_output, result_output)

    output = output_writer.ReadOutput()
    self.assertIn('Processing completed.', output)


if __name__ == '__main__':
  unittest.main()
