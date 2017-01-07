#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline CLI tool."""

import argparse
import os
import unittest

from plaso.lib import errors
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib

from tools import log2timeline


class Log2TimelineToolTest(cli_test_lib.CLIToolTestCase):
  """Tests for the log2timeline CLI tool."""

  _BDE_PASSWORD = u'bde-TEST'

  _EXPECTED_PROCESSING_OPTIONS = u'\n'.join([
      u'usage: log2timeline_test.py [--single_process] [--disable_zeromq]',
      u'                            [--workers WORKERS]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --disable_zeromq, --disable-zeromq',
      (u'                        Disable queueing using ZeroMQ. A '
       u'Multiprocessing queue'),
      u'                        will be used instead.',
      u'  --single_process, --single-process',
      (u'                        Indicate that the tool should run in a '
       u'single process.'),
      (u'  --workers WORKERS     The number of worker threads [defaults to '
       u'available'),
      u'                        system CPUs minus one].',
      u''])

  # TODO: add test for _GetMatcher.
  # TODO: add test for _ParseOutputOptions.
  # TODO: add test for _ParseProcessingOptions.

  def testAddProcessingOptions(self):
    """Tests the AddProcessingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'log2timeline_test.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    test_tool = log2timeline.Log2TimelineTool()
    test_tool.AddProcessingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PROCESSING_OPTIONS)

  def testListHashers(self):
    """Tests the ListHashers function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    test_tool.ListHashers()

    output = output_writer.ReadOutput()

    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    self.assertIn(u'Hashers', lines[1])

    lines = frozenset(lines)

    self.assertEqual(number_of_tables, 1)

    expected_line = b'md5 : Calculates an MD5 digest hash over input data.'
    self.assertIn(expected_line, lines)

  def testListOutputModules(self):
    """Tests the ListOutputModules function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    test_tool.ListOutputModules()

    output = output_writer.ReadOutput()
    number_of_tables = 0
    lines = []
    for line in output.split(b'\n'):
      line = line.strip()
      lines.append(line)

      if line.startswith(b'*****') and line.endswith(b'*****'):
        number_of_tables += 1

    self.assertIn(u'Output Modules', lines[1])

    # pylint: disable=protected-access
    lines = frozenset(lines)
    disabled_outputs = list(test_tool._front_end.GetDisabledOutputClasses())
    enabled_outputs = list(test_tool._front_end.GetOutputClasses())

    expected_number_of_tables = 0
    if disabled_outputs:
      expected_number_of_tables += 1
    if enabled_outputs:
      expected_number_of_tables += 1

    self.assertEqual(number_of_tables, expected_number_of_tables)

    expected_line = b'rawpy : "raw" (or native) Python output.'
    self.assertIn(expected_line, lines)

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

    self.assertIn(u'Parsers', lines[1])

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

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
    options.source = self._GetTestFilePath([u'testdir'])
    options.output = u'storage.plaso'

    test_tool.ParseOptions(options)

    options = cli_test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options = cli_test_lib.TestOptions()
    options.source = self._GetTestFilePath([u'testdir'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

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
    test_tool = log2timeline.Log2TimelineTool(output_writer=output_writer)

    options = cli_test_lib.TestOptions()
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
