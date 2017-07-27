#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psteal CLI tool."""

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

  _BDE_PASSWORD = u'bde-TEST'

  _EXPECTED_PROCESSING_OPTIONS = u'\n'.join([
      u'usage: psteal_test.py',
      u'',
      u'Test argument parser.',
      u''])

  _STORAGE_FILENAME_TEMPLATE = r'\d{{8}}T\d{{6}}-{filename}.plaso'

  def testGenerateStorageFileName(self):
    """Tests the _GenerateStorageFileName function."""
    test_tool = psteal_tool.PstealTool()

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
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])

    # Test when the output file is missing.
    expected_error = (u'Output format: dynamic requires an output file')
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

    options.write = u'dynamic.out'

    # Test when the source is missing.
    expected_error = u'Missing source path.'
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

    with shared_test_lib.TempDirectory() as temp_directory:
      options.source = self._GetTestFilePath([u'testdir'])
      options.write = os.path.join(temp_directory, u'dynamic.out')

      # Test when both source and output are specified.
      test_tool.ParseOptions(options)

      with open(options.write, 'w') as file_object:
        file_object.write(u'bogus')

      # Test when output file already exists.
      # Escape \ otherwise assertRaisesRegexp can error with:
      # error: bogus escape: u'\\1'
      expected_error = u'Output file already exists: {0:s}.'.format(
          options.write.replace(u'\\', u'\\\\'))
      with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
        test_tool.ParseOptions(options)

  def testParseArguments(self):
    """Tests the ParseArguments function"""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    # Test ParseArguments with no output file nor source.
    result = test_tool.ParseArguments()
    self.assertFalse(result)
    output = output_writer.ReadOutput()
    expected_error = u'ERROR: Output format: dynamic requires an output file'
    self.assertIn(expected_error, output)

  def testExtractEventsFromSourceDirectory(self):
    """Tests the ExtractEventsFromSources function on a directory."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.quiet = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'testdir'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.write = os.path.join(temp_directory, u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
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

    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.credentials = [u'password:{0:s}'.format(self._BDE_PASSWORD)]
    options.quiet = True
    options.source = self._GetTestFilePath([u'bdetogo.raw'])
    options.status_view_mode = u'none'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.write = os.path.join(temp_directory, u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
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
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.quiet = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'ímynd.dd'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.write = os.path.join(temp_directory, u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
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
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.partitions = u'all'
    options.quiet = True
    options.status_view_mode = u'none'
    # Note that the source file is a RAW (VMDK flat) image.
    options.source = self._GetTestFilePath([u'multi_partition_image.vmdk'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.write = os.path.join(temp_directory, u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
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
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'vsstest.qcow2'])
    options.vss_stores = u'all'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.write = os.path.join(temp_directory, u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
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
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.quiet = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'System.evtx'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.write = os.path.join(temp_directory, u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      expected_output = [
          b'',
          b'Source path\t: {0:s}'.format(options.source.encode(u'utf-8')),
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
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal_tool.PstealTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.storage_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    options.source = u'unused_source'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.write = os.path.join(temp_directory, u'output.txt')

      test_tool.ParseOptions(options)
      test_tool.AnalyzeEvents()

      expected_output_file_name = self._GetTestFilePath(
          [u'end_to_end', u'dynamic.log'])
      with open(expected_output_file_name, 'rb') as file_object:
        expected_output = file_object.read()

      with open(options.write, 'rb') as file_object:
        result_output = file_object.read()

      expected_output = sorted(expected_output.split(b'\n'))
      result_output = sorted(result_output.split(b'\n'))
      self.assertEqual(expected_output, result_output)

    output = output_writer.ReadOutput()
    self.assertIn(u'Events processed : 38', output)


if __name__ == '__main__':
  unittest.main()
