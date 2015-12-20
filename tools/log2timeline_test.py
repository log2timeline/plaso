#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline CLI tool."""

import os
import unittest

from plaso.storage import zip_file as storage_zip_file

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
    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'testdir'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'test.plaso')

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesBDEImage(self):
    """Tests the ProcessSources function on an image containing BDE."""
    options = cli_test_lib.TestOptions()
    options.credentials = [u'password:{0:s}'.format(self._BDE_PASSWORD)]
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'bdetogo.raw'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'test.plaso')

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesImage(self):
    """Tests the ProcessSources function on a single partition image."""
    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'ímynd.dd'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'test.plaso')

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesPartitionedImage(self):
    """Tests the ProcessSources function on a multi partition image."""
    options = cli_test_lib.TestOptions()
    # TODO: refactor to partitions.
    options.partition_number = u'all'
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    # Note that the source file is a RAW (VMDK flat) image.
    options.source = self._GetTestFilePath([u'multi_partition_image.vmdk'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'test.plaso')

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesVSSImage(self):
    """Tests the ProcessSources function on an image containing VSS."""
    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'vsstest.qcow2'])
    options.vss_stores = u'all'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'test.plaso')

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesSingleFile(self):
    """Tests the ProcessSources function on a single file."""
    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'System.evtx'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'test.plaso')

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      output = self._output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesFilestat(self):
    """Test if the filestat and other parsers ran."""
    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.parsers = u'filestat,pe'
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'test_pe.exe'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'test.plaso')

      self._test_tool.ParseOptions(options)

      self._test_tool.ProcessSources()

      try:
        storage_file = storage_zip_file.StorageFile(
            options.output, read_only=True)
      except IOError:
        self.fail(u'Unable to open storage file after processing.')

      event_objects = []
      event_object = storage_file.GetSortedEntry()
      while event_object:
        event_objects.append(event_objects)
        event_object = storage_file.GetSortedEntry()

      # There should be 3 filestat and 3 pe parser generated events.
      self.assertEquals(len(event_objects), 6)

  def testShowInfo(self):
    """Tests the output of the tool in info mode."""
    options = cli_test_lib.TestOptions()
    options.show_info = True
    self._test_tool.ParseOptions(options)
    self._test_tool.ShowInfo()
    output = self._output_writer.ReadOutput()

    section_headings = [
        u'Parser Presets', u'Hashers', u'Parser Plugins', u'Versions',
        u'Filters', u'Parsers', u'Output Modules']
    for heading in section_headings:
      self.assertIn(heading, output)

    self.assertNotIn(u'<class', output)


if __name__ == '__main__':
  unittest.main()
