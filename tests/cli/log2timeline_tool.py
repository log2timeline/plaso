#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline CLI tool."""

import argparse
import os
import unittest

from plaso.cli import log2timeline_tool
from plaso.lib import definitions
from plaso.lib import errors
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class Log2TimelineToolTest(test_lib.CLIToolTestCase):
  """Tests for the log2timeline CLI tool."""

  # pylint: disable=protected-access

  _BDE_PASSWORD = u'bde-TEST'

  _EXPECTED_PROCESSING_OPTIONS = u'\n'.join([
      u'usage: log2timeline_test.py [--disable_zeromq] [--single_process]',
      u'                            [--temporary_directory DIRECTORY]',
      (u'                            [--worker-memory-limit SIZE] '
       u'[--workers WORKERS]'),
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
      u'  --temporary_directory DIRECTORY, --temporary-directory DIRECTORY',
      (u'                        Path to the directory that should be used to '
       u'store'),
      u'                        temporary files created during processing.',
      u'  --worker-memory-limit SIZE, --worker_memory_limit SIZE',
      (u'                        Maximum amount of memory a worker process is '
       u'allowed'),
      u'                        to consume. [defaults to 2 GiB]',
      (u'  --workers WORKERS     The number of worker processes [defaults to '
       u'available'),
      u'                        system CPUs minus one].',
      u''])

  # TODO: add tests for _CheckStorageFile
  # TODO: add tests for _CreateProcessingConfiguration

  def testGetPluginData(self):
    """Tests the _GetPluginData function."""
    test_tool = log2timeline_tool.Log2TimelineTool()
    plugin_info = test_tool._GetPluginData()

    self.assertIn(u'Hashers', plugin_info)

    available_hasher_names = [name for name, _ in plugin_info[u'Hashers']]
    self.assertIn(u'sha256', available_hasher_names)
    self.assertIn(u'sha1', available_hasher_names)

    self.assertIn(u'Parsers', plugin_info)
    self.assertIsNotNone(plugin_info[u'Parsers'])

    self.assertIn(u'Parser Plugins', plugin_info)
    self.assertIsNotNone(plugin_info[u'Parser Plugins'])

  def testParseProcessingOptions(self):
    """Tests the _ParseProcessingOptions function."""
    test_tool = log2timeline_tool.Log2TimelineTool()

    options = test_lib.TestOptions()

    test_tool._ParseProcessingOptions(options)

  # TODO: add tests for _PrintProcessingSummary

  def testAddProcessingOptions(self):
    """Tests the AddProcessingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'log2timeline_test.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = log2timeline_tool.Log2TimelineTool()
    test_tool.AddProcessingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PROCESSING_OPTIONS)

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  @shared_test_lib.skipUnlessHasTestFile([u'testdir'])
  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.source = self._GetTestFilePath([u'testdir'])
    options.storage_file = u'storage.plaso'
    options.storage_format = definitions.STORAGE_FORMAT_ZIP

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])

    # ParseOptions will raise if source is not set.
    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.source = self._GetTestFilePath([u'testdir'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  def testExtractEventsFromSourcesOnDirectory(self):
    """Tests the ExtractEventsFromSources function on a directory."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'testdir'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_ZIP

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

  def testExtractEventsFromSourcesOnBDEImage(self):
    """Tests the ExtractEventsFromSources function on BDE image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.credentials = [u'password:{0:s}'.format(self._BDE_PASSWORD)]
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'bdetogo.raw'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_ZIP

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
    """Tests the ExtractEventsFromSources function on single partition image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'ímynd.dd'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_ZIP

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

  def testExtractEventsFromSourcesPartitionedImage(self):
    """Tests the ExtractEventsFromSources function on multi partition image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.partitions = u'all'
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    # Note that the source file is a RAW (VMDK flat) image.
    options.source = self._GetTestFilePath([u'multi_partition_image.vmdk'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_ZIP

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

  def testExtractEventsFromSourcesOnVSSImage(self):
    """Tests the ExtractEventsFromSources function on VSS image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'vsstest.qcow2'])
    options.vss_stores = u'all'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_ZIP

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

  def testExtractEventsFromSourcesOnFile(self):
    """Tests the ExtractEventsFromSources function on a file."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.quiet = True
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'System.evtx'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_ZIP

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

  def testExtractEventsFromSourcesWithFilestat(self):
    """Tests the ExtractEventsFromSources function with filestat parser."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.quiet = True
    options.parsers = u'filestat,pe'
    options.single_process = True
    options.status_view_mode = u'none'
    options.source = self._GetTestFilePath([u'test_pe.exe'])

    with shared_test_lib.TempDirectory() as temp_directory:
      options.storage_file = os.path.join(temp_directory, u'storage.plaso')
      options.storage_format = definitions.STORAGE_FORMAT_ZIP

      test_tool.ParseOptions(options)

      test_tool.ExtractEventsFromSources()

      storage_file = storage_zip_file.ZIPStorageFile()
      try:
        storage_file.Open(path=options.storage_file, read_only=True)
      except IOError as exception:
        self.fail((
            u'Unable to open storage file after processing with error: '
            u'{0:s}.').format(exception))

      # There should be 3 filestat and 3 pe parser generated events.
      events = list(storage_file.GetSortedEvents())
      self.assertEqual(len(events), 6)

  def testShowInfo(self):
    """Tests the output of the tool in info mode."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = log2timeline_tool.Log2TimelineTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.show_info = True

    test_tool.ParseOptions(options)
    test_tool.ShowInfo()

    output = output_writer.ReadOutput()

    section_headings = [
        u'Hashers', u'Parsers', u'Parser Plugins', u'Parser Presets',
        u'Versions']
    for heading in section_headings:
      self.assertIn(heading, output)

    self.assertNotIn(u'<class', output)


if __name__ == '__main__':
  unittest.main()
