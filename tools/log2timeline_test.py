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

  # TODO: add test for _FormatStatusTableRow.
  # TODO: add test for _GetMatcher.
  # TODO: add test for _ParseExperimentalOptions.
  # TODO: add test for _ParseOutputOptions.
  # TODO: add test for _ParseProcessingOptions.
  # TODO: add test for _PrintStatusUpdate.
  # TODO: add test for _PrintStatusUpdateStream.
  # TODO: add test for AddExperimentalOptions.
  # TODO: add test for AddProcessingOptions.
  # TODO: add test for ListHashers.

  def testListOutputModules(self):
    """Tests the ListOutputModules function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    test_tool.ListOutputModules()

    output = output_writer.ReadOutput()

    expected_output = b''

    # Compare the output as list of lines which makes it easier to spot
    # differences.

    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))

  def testListParsersAndPlugins(self):
    """Tests the ListParsersAndPlugins function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    test_tool.ListParsersAndPlugins()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 9)

    expected_line = b'filestat : Parser for file system stat information.'
    self.assertIn(expected_line, lines)

    expected_line = b'bencode_utorrent : Parser for uTorrent bencoded files.'
    self.assertIn(expected_line, lines)

    expected_line = (
        b'msie_webcache : Parser for MSIE WebCache ESE database files.')
    self.assertIn(expected_line, lines)

    expected_line = b'olecf_default : Parser for a generic OLECF item.'
    self.assertIn(expected_line, lines)

    expected_line = b'plist_default : Parser for plist files.'
    self.assertIn(expected_line, lines)

    expected_line = (
        b'chrome_history : Parser for Chrome history SQLite database files.')
    self.assertIn(expected_line, lines)

    expected_line = b'ssh : Parser for SSH syslog entries.'
    self.assertIn(expected_line, lines)

    expected_line = b'winreg_default : Parser for Registry data.'
    self.assertIn(expected_line, lines)

  # TODO: add test for ParseArguments.
  # TODO: add test for ParseOptions.

  def testProcessSourcesDirectory(self):
    """Tests the ProcessSources function on a directory."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'testdir'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      output = output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesBDEImage(self):
    """Tests the ProcessSources function on an image containing BDE."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.credentials = [u'password:{0:s}'.format(self._BDE_PASSWORD)]
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'bdetogo.raw'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      output = output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesImage(self):
    """Tests the ProcessSources function on a single partition image."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'ímynd.dd'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      output = output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesPartitionedImage(self):
    """Tests the ProcessSources function on a multi partition image."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    # TODO: refactor to partitions.
    options.partitions = u'all'
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    # Note that the source file is a RAW (VMDK flat) image.
    options.source = self._GetTestFilePath([u'multi_partition_image.vmdk'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      output = output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesVSSImage(self):
    """Tests the ProcessSources function on an image containing VSS."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'vsstest.qcow2'])
    options.vss_stores = u'all'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      output = output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesSingleFile(self):
    """Tests the ProcessSources function on a single file."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'System.evtx'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      output = output_writer.ReadOutput()
      # TODO: print summary and compare that against output.
      _ = output

  def testProcessSourcesFilestat(self):
    """Test if the filestat and other parsers ran."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.quiet = True
    options.parsers = u'filestat,pe'
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'test_pe.exe'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.output = os.path.join(temp_directory, u'storage.plaso')

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      storage_file = storage_zip_file.ZIPStorageFile()
      try:
        storage_file.Open(path=options.output, read_only=True)
      except IOError as exception:
        self.fail((
            u'Unable to open storage file after processing with error: '
            u'{0:s}.').format(exception))

      # There should be 3 filestat and 3 pe parser generated events.
      event_objects = list(storage_file.GetEvents())
      self.assertEquals(len(event_objects), 6)

  def testShowInfo(self):
    """Tests the output of the tool in info mode."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.show_info = True
    test_tool.ParseOptions(options)
    test_tool.ShowInfo()
    output = output_writer.ReadOutput()

    section_headings = [
        u'Parser Presets', u'Hashers', u'Parser Plugins', u'Versions',
        u'Filters', u'Parsers', u'Output Modules']
    for heading in section_headings:
      self.assertIn(heading, output)

    self.assertNotIn(u'<class', output)


if __name__ == '__main__':
  unittest.main()
