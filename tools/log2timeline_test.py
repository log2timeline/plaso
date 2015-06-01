#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline CLI tool."""

import os
import unittest

from plaso.cli import test_lib as cli_test_lib
from plaso.frontend import frontend
from tools import log2timeline


class Log2TimelineToolTest(cli_test_lib.CLIToolTestCase):
  """Tests for the log2timeline CLI tool."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    self._test_tool = log2timeline.Log2TimelineTool(
        output_writer=self._output_writer)

  def testProcessSourcesDirectory(self):
    """Tests the ProcessSources function on a directory."""
    options = frontend.Options()
    test_source = self._GetTestFilePath([u'testdir'])

    with cli_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

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
    options = frontend.Options()
    test_source = self._GetTestFilePath([u'image.qcow2'])

    with cli_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

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
    options = frontend.Options()
    test_source = self._GetTestFilePath([u'multi_partition_image.vmdk'])

    with cli_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

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
    options = frontend.Options()
    test_source = self._GetTestFilePath([u'vsstest.qcow2'])

    with cli_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

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
    options = frontend.Options()
    test_source = self._GetTestFilePath([u'System.evtx'])

    with cli_test_lib.TempDirectory() as temp_directory:
      test_storage_file = os.path.join(temp_directory, u'test.plaso')

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
