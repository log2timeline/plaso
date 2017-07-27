#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the image export CLI tool."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.cli import image_export_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as test_lib


class ImageExportToolTest(test_lib.CLIToolTestCase):
  """Tests for the image export CLI tool."""

  # pylint: disable=protected-access

  def _GetTestScanNode(self, scan_context):
    """Retrieves the scan node for testing.

    Retrieves the first scan node, from the root upwards, with more or less
    than 1 sub node.

    Args:
      scan_context (dfvfs.SourceScanContext): scan context.

    Returns:
      dfvfs.SourceScanNode: scan node.
    """
    scan_node = scan_context.GetRootScanNode()
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    return scan_node

  def _RecursiveList(self, path):
    """Recursively lists a file or directory.

    Args:
      path (str): path of the file or directory to list.

    Returns:
      list[str]: names of files and sub directories within the path.
    """
    results = []
    for sub_path, _, files in os.walk(path):
      if sub_path != path:
        results.append(sub_path)

      for file_entry in files:
        results.append(os.path.join(sub_path, file_entry))

    return results

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testCalculateDigestHash(self):
    """Tests the _CalculateDigestHash function."""
    test_tool = image_export_tool.ImageExportTool()

    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    digest_hash = test_tool._CalculateDigestHash(file_entry, u'')
    expected_digest_hash = (
        u'c7fbc0e821c0871805a99584c6a384533909f68a6bbe9a2a687d28d9f3b10c16')
    self.assertEqual(digest_hash, expected_digest_hash)

    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=12,
        location=u'/a_directory', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    with self.assertRaises(IOError):
      test_tool._CalculateDigestHash(file_entry, u'')

  # TODO: add tests for _CreateSanitizedDestination.
  # TODO: add tests for _Extract.

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testExtractDataStream(self):
    """Tests the _ExtractDataStream function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool()

    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    with shared_test_lib.TempDirectory() as temp_directory:
      test_tool._ExtractDataStream(
          file_entry, u'', temp_directory, output_writer)

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testExtractFileEntry(self):
    """Tests the _ExtractFileEntry function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool()

    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_tool._ExtractFileEntry(
          tsk_path_spec, temp_directory, output_writer)

  # TODO: add tests for _ExtractWithFilter.
  # TODO: add tests for _GetSourceFileSystem.

  def testParseExtensionsString(self):
    """Tests the _ParseExtensionsString function."""
    test_tool = image_export_tool.ImageExportTool()

    test_tool._ParseExtensionsString(u'txt')

  # TODO: add tests for _ParseFilterOptions.

  def testParseNamesString(self):
    """Tests the _ParseNamesString function."""
    test_tool = image_export_tool.ImageExportTool()

    test_tool._ParseNamesString(u'another_file')

  def testParseSignatureIdentifiers(self):
    """Tests the _ParseSignatureIdentifiers function."""
    test_tool = image_export_tool.ImageExportTool()

    test_tool._ParseSignatureIdentifiers(self._DATA_PATH, u'gzip')

    with self.assertRaises(ValueError):
      test_tool._ParseSignatureIdentifiers(None, u'gzip')

    with self.assertRaises(IOError):
      test_path = os.path.join(os.sep, u'bogus')
      test_tool._ParseSignatureIdentifiers(test_path, u'gzip')

  # TODO: add tests for _Preprocess.
  # TODO: add tests for _ReadSpecificationFile.

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testWriteFileEntry(self):
    """Tests the _WriteFileEntry function."""
    test_tool = image_export_tool.ImageExportTool()

    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    with shared_test_lib.TempDirectory() as temp_directory:
      destination_path = os.path.join(temp_directory, u'another_file')
      test_tool._WriteFileEntry(file_entry, u'', destination_path)

  # TODO: add tests for AddFilterOptions.

  def testListSignatureIdentifiers(self):
    """Tests the ListSignatureIdentifiers function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    test_tool._data_location = self._TEST_DATA_PATH

    test_tool.ListSignatureIdentifiers()

    expected_output = (
        b'Available signature identifiers:\n'
        b'7z, bzip2, esedb, evt, evtx, ewf_e01, ewf_l01, exe_mz, gzip, lnk, '
        b'msiecf, nk2,\n'
        b'olecf, olecf_beta, pdf, pff, qcow, rar, regf, tar, tar_old, '
        b'vhdi_footer,\n'
        b'vhdi_header, wtcdb_cache, wtcdb_index, zip\n'
        b'\n')

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))

    test_tool._data_location = self._GetTestFilePath([u'tmp'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ListSignatureIdentifiers()

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'image.qcow2'])

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testPrintFilterCollection(self):
    """Tests the PrintFilterCollection function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.date_filters = [u'ctime,2012-05-25 15:59:00,2012-05-25 15:59:20']
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.quiet = True

    test_tool.ParseOptions(options)

    test_tool.PrintFilterCollection()

    expected_output = b'\n'.join([
        b'Filters:',
        (b'\tctime between 2012-05-25T15:59:00+00:00 and '
         b'2012-05-25T15:59:20+00:00'),
        b''])
    output = output_writer.ReadOutput()
    self.assertEqual(output, expected_output)

  def testProcessSourcesWithImage(self):
    """Tests the ProcessSources function on a single partition image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'ímynd.dd'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_output = b'\n'.join([
          b'Export started.',
          b'Extracting file entries.',
          b'Export completed.',
          b'',
          b''])

      output = output_writer.ReadOutput()
      self.assertEqual(output, expected_output)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithDateTimeFilter(self):
    """Tests the ProcessSources function with a date time filter."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.date_filters = [u'ctime,2012-05-25 15:59:00,2012-05-25 15:59:20']
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'a_directory'),
          os.path.join(temp_directory, u'a_directory', u'a_file')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithExtensionsFilter(self):
    """Tests the ProcessSources function with an extensions filter."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.extensions_string = u'txt'
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'passwords.txt')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithNamesFilter(self):
    """Tests the ProcessSources function with a names filter."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.names_string = u'another_file'
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'a_directory'),
          os.path.join(temp_directory, u'a_directory', u'another_file')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithFilter(self):
    """Tests the ProcessSources function with a filter file."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      filter_file = os.path.join(temp_directory, u'filter.txt')
      with open(filter_file, 'wb') as file_object:
        file_object.write(b'/a_directory/.+_file\n')

      options.file_filter = filter_file
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'filter.txt'),
          os.path.join(temp_directory, u'a_directory'),
          os.path.join(temp_directory, u'a_directory', u'another_file'),
          os.path.join(temp_directory, u'a_directory', u'a_file')])

      extracted_files = self._RecursiveList(temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_image.dd'])
  def testProcessSourcesExtractWithSignaturesFilter(self):
    """Tests the ProcessSources function with a signatures filter."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = self._GetTestFilePath([u'artifacts'])
    options.image = self._GetTestFilePath([u'syslog_image.dd'])
    options.quiet = True
    options.signature_identifiers = u'gzip'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'logs'),
          os.path.join(temp_directory, u'logs', u'sys.tgz')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)


if __name__ == '__main__':
  unittest.main()
