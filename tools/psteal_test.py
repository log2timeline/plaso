#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psteal CLI tool."""

import os
import unittest

from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib

from tools import psteal


class PstealToolTest(cli_test_lib.CLIToolTestCase):
  """Tests for the psteal CLI tool."""

  _BDE_PASSWORD = u'bde-TEST'

  _EXPECTED_PROCESSING_OPTIONS = u'\n'.join([
      u'usage: psteal_test.py',
      u'',
      u'Test argument parser.',
      u''])

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal.PstealTool(output_writer=output_writer)

    # Test when no source nor output file specified.
    options = cli_test_lib.TestOptions()
    expected_error = u'Missing source path.'
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

    # Test when the source is missing.
    options = cli_test_lib.TestOptions()
    expected_error = u'Missing source path.'
    with shared_test_lib.TempDirectory() as temp_directory:
      options.analysis_output_file = os.path.join(temp_directory,
                                                  u'unused_output.txt')
      with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
        test_tool.ParseOptions(options)

    # Test when the output file is missing.
    options.source = self._GetTestFilePath([u'testdir'])
    expected_error = (u'Output format: dynamic requires an output file.')
    with self.assertRaisesRegexp(errors.BadConfigOption, expected_error):
      test_tool.ParseOptions(options)

    # Test when both source and output are specified.
    options = cli_test_lib.TestOptions()
    options.source = self._GetTestFilePath([u'testdir'])
    with shared_test_lib.TempDirectory() as temp_directory:
      options.analysis_output_file = os.path.join(temp_directory,
                                                  u'unused_output.txt')
      test_tool.ParseOptions(options)

  def testParseArguments(self):
    """Tests the ParseArguments function"""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal.PstealTool(output_writer=output_writer)

    # Test ParseArguments with no output file nor source.
    result = test_tool.ParseArguments()
    self.assertFalse(result)
    output = output_writer.ReadOutput()
    expected_error = u'ERROR: Missing source path'
    self.assertIn(expected_error, output)

  def testProcessSourcesDirectory(self):
    """Tests the ProcessSources function on a directory."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal.PstealTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'testdir'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.analysis_output_file = os.path.join(temp_directory,
                                                  u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

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

  def testProcessSourcesBDEImage(self):
    """Tests the ProcessSources function on an image containing BDE."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal.PstealTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.credentials = [u'password:{0:s}'.format(self._BDE_PASSWORD)]
    options.quiet = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'bdetogo.raw'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.analysis_output_file = os.path.join(temp_directory,
                                                  u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

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

  def testProcessSourcesImage(self):
    """Tests the ProcessSources function on a single partition image."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal.PstealTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'ímynd.dd'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.analysis_output_file = os.path.join(temp_directory,
                                                  u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

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

  def testProcessSourcesPartitionedImage(self):
    """Tests the ProcessSources function on a multi partition image."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal.PstealTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    # TODO: refactor to partitions.
    options.partitions = u'all'
    options.quiet = True
    options.status_view_mode = u'none'
    # Note that the source file is a RAW (VMDK flat) image.
    options.source = self._GetTestFilePath([u'multi_partition_image.vmdk'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.analysis_output_file = os.path.join(temp_directory,
                                                  u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

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

  def testProcessSourcesVSSImage(self):
    """Tests the ProcessSources function on an image containing VSS."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal.PstealTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'vsstest.qcow2'])
    options.vss_stores = u'all'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.analysis_output_file = os.path.join(temp_directory,
                                                  u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

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

  def testProcessSourcesSingleFile(self):
    """Tests the ProcessSources function on a single file."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal.PstealTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'System.evtx'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.analysis_output_file = os.path.join(temp_directory,
                                                  u'unused_output.txt')
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

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
    """Test the ProcessStorage function"""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = psteal.PstealTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    options.source = u'unused_source'

    with shared_test_lib.TempDirectory() as temp_directory:
      result_file_name = os.path.join(temp_directory, u'output.txt')
      options.analysis_output_file = result_file_name

      test_tool.ParseOptions(options)
      test_tool.ProcessStorage()

      expected_output_file_name = self._GetTestFilePath(
          [u'end_to_end', u'dynamic.log'])
      with open(expected_output_file_name, 'r') as expected_output_file, open(
          result_file_name, 'r') as result_file:
        expected_output = expected_output_file.read()
        result = result_file.read()
        self.assertEqual(expected_output, result)

    output = output_writer.ReadOutput()
    self.assertIn(u'Events processed : 38', output)


if __name__ == '__main__':
  unittest.main()
