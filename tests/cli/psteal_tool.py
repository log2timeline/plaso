#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psteal CLI tool."""

from __future__ import unicode_literals

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

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.curdir = os.path.realpath(os.path.curdir)

  def tearDown(self):
    """Cleans up after running an individual test."""
    os.chdir(self.curdir)

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
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.storage_file = self._GetTestFilePath(['psort_test.json.plaso'])
    options.source = 'unused_source'

    with shared_test_lib.TempDirectory() as temp_directory:
      os.chdir(temp_directory)
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
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.source = 'source'
    # Test when the output file is missing.
    expected_error = ('Output format: dynamic requires an output file')
    # pylint: disable=deprecated-method
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

    options = test_lib.TestOptions()
    options.write = 'output.csv'
    # Test when the source is missing.
    expected_error = ('Missing source path.')
    # pylint: disable=deprecated-method
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

    # Test when the source is missing.
    expected_error = 'Missing source path.'
    # pylint: disable=deprecated-method
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

  def testParseArguments(self):
    """Tests the ParseArguments function"""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    # Test ParseArguments with no output file nor source.
    result = test_tool.ParseArguments()
    self.assertFalse(result)
    output = output_writer.ReadOutput()
    expected_error = 'Output format: dynamic requires an output file'
    self.assertIn(expected_error, output)

  def testExtractEventsFromSourceDirectory(self):
    """Tests the ExtractEventsFromSources function on a directory."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.quiet = True
    options.status_view_mode = 'none'
    options.source = self._GetTestFilePath(['testdir'])

    with shared_test_lib.TempDirectory() as temp_directory:
      os.chdir(temp_directory)
      options.write = os.path.join(temp_directory, 'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode('utf-8')),
          b'Source type\t: directory',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourceBDEImage(self):
    """Tests the ExtractEventsFromSources function on an image with BDE."""
    # TODO: added for testing.
    dfvfs_resolver.Resolver.key_chain.Empty()

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.credentials = ['password:{0:s}'.format(self._BDE_PASSWORD)]
    options.quiet = True
    options.source = self._GetTestFilePath(['bdetogo.raw'])
    options.status_view_mode = 'none'

    with shared_test_lib.TempDirectory() as temp_directory:
      os.chdir(temp_directory)
      options.write = os.path.join(temp_directory, 'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode('utf-8')),
          b'Source type\t: storage media image',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourcesImage(self):
    """Tests the ExtractEventsFromSources function on a single partition."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.quiet = True
    options.status_view_mode = 'none'
    options.source = self._GetTestFilePath(['ímynd.dd'])

    with shared_test_lib.TempDirectory() as temp_directory:
      os.chdir(temp_directory)
      options.write = os.path.join(temp_directory, 'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode('utf-8')),
          b'Source type\t: storage media image',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourcePartitionedImage(self):
    """Tests the ExtractEventsFromSources function on a multi partition
    image."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.partitions = 'all'
    options.quiet = True
    options.status_view_mode = 'none'
    # Note that the source file is a RAW (VMDK flat) image.
    options.source = self._GetTestFilePath(['multi_partition_image.vmdk'])

    with shared_test_lib.TempDirectory() as temp_directory:
      os.chdir(temp_directory)
      options.write = os.path.join(temp_directory, 'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode('utf-8')),
          b'Source type\t: storage media image',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourceVSSImage(self):
    """Tests the ExtractEventsFromSources function on an image with VSS."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.quiet = True
    options.single_process = True
    options.status_view_mode = 'none'
    options.source = self._GetTestFilePath(['vsstest.qcow2'])
    options.vss_stores = 'all'

    with shared_test_lib.TempDirectory() as temp_directory:
      os.chdir(temp_directory)
      options.write = os.path.join(temp_directory, 'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode('utf-8')),
          b'Source type\t: storage media image',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'Number of errors encountered while extracting events: 1.',
          b'',
          b'Use pinfo to inspect errors in more detail.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testExtractEventsFromSourceSingleFile(self):
    """Tests the ExtractEventsFromSources function on a single file."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.quiet = True
    options.status_view_mode = 'none'
    options.source = self._GetTestFilePath(['System.evtx'])

    with shared_test_lib.TempDirectory() as temp_directory:
      os.chdir(temp_directory)
      options.write = os.path.join(temp_directory, 'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, 'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode('utf-8')),
          b'Source type\t: single file',
          b'',
          b'Processing started.',
          b'Processing completed.',
          b'',
          b'']

      output = output_writer.ReadOutput()
      self.assertEqual(output.split(b'\n'), expected_output)

  def testProcessStorage(self):
    """Test the AnalyzeEvents function"""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath(['artifacts'])
    options.storage_file = self._GetTestFilePath(['psort_test.json.plaso'])
    options.source = 'unused_source'

    with shared_test_lib.TempDirectory() as temp_directory:
      os.chdir(temp_directory)
      options.write = os.path.join(temp_directory, 'output.txt')

      test_tool.ParseOptions(options)
      test_tool.AnalyzeEvents()

      expected_output_file_name = self._GetTestFilePath(
          ['end_to_end', 'dynamic.log'])
      with open(expected_output_file_name, 'rb') as file_object:
        expected_output = file_object.read()

      with open(options.write, 'rb') as file_object:
        result_output = file_object.read()

      expected_output = sorted(expected_output.split(b'\n'))
      result_output = sorted(result_output.split(b'\n'))
      self.assertEqual(expected_output, result_output)

    output = output_writer.ReadOutput()
    self.assertIn('Events processed : 38', output)


if __name__ == '__main__':
  unittest.main()
