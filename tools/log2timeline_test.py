#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline CLI tool."""

import os
import unittest

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib

from tools import log2timeline


class Log2TimelineToolTest(cli_test_lib.CLIToolTestCase):
  """Tests for the log2timeline CLI tool."""

  _BDE_PASSWORD = u'bde-TEST'

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    self._test_tool = log2timeline.Log2TimelineTool(
        output_writer=self._output_writer)

  def testProcessSourcesDirectory(self):
    """Tests the ProcessSources function on a directory."""
    test_source = self._GetTestFilePath([u'testdir'])

    with shared_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

      options = cli_test_lib.TestOptions()
      options.output = test_storage_file
      options.quiet = True
      options.single_process = True
      options.status_view_mode = u'none'
      options.source = test_source

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesBDEImage(self):
    """Tests the ProcessSources function on an image containing BDE."""
    test_source = self._GetTestFilePath([u'bdetogo.raw'])

    with shared_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

      options = cli_test_lib.TestOptions()
      options.credentials = [u'password:{0:s}'.format(self._BDE_PASSWORD)]
      options.output = test_storage_file
      options.quiet = True
      options.single_process = True
      options.status_view_mode = u'none'
      options.source = test_source

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesImage(self):
    """Tests the ProcessSources function on a single partition image."""
    test_source = self._GetTestFilePath([u'image.qcow2'])

    with shared_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

      options = cli_test_lib.TestOptions()
      options.output = test_storage_file
      options.quiet = True
      options.single_process = True
      options.status_view_mode = u'none'
      options.source = test_source

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesPartitionedImage(self):
    """Tests the ProcessSources function on a multi partition image."""
    # Note that the source file is a RAW (VMDK flat) image.
    test_source = self._GetTestFilePath([u'multi_partition_image.vmdk'])

    with shared_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

      options = cli_test_lib.TestOptions()
      # TODO: refactor to partitions.
      options.partition_number = u'all'
      options.output = test_storage_file
      options.quiet = True
      options.single_process = True
      options.status_view_mode = u'none'
      options.source = test_source

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesVSSImage(self):
    """Tests the ProcessSources function on an image containing VSS."""
    test_source = self._GetTestFilePath([u'vsstest.qcow2'])

    with shared_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

      options = cli_test_lib.TestOptions()
      options.output = test_storage_file
      options.quiet = True
      options.single_process = True
      options.status_view_mode = u'none'
      options.source = test_source
      options.vss_stores = u'all'

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesSingleFile(self):
    """Tests the ProcessSources function on a single file."""
    test_source = self._GetTestFilePath([u'System.evtx'])

    with shared_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

      options = cli_test_lib.TestOptions()
      options.output = test_storage_file
      options.quiet = True
      options.single_process = True
      options.status_view_mode = u'none'
      options.source = test_source

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output


if __name__ == '__main__':
  unittest.main()
