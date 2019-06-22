#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the image export CLI tool."""

from __future__ import unicode_literals

import io
import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.cli import image_export_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


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

  def testCalculateDigestHash(self):
    """Tests the _CalculateDigestHash function."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    test_tool = image_export_tool.ImageExportTool()

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location='/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    digest_hash = test_tool._CalculateDigestHash(file_entry, '')
    expected_digest_hash = (
        'c7fbc0e821c0871805a99584c6a384533909f68a6bbe9a2a687d28d9f3b10c16')
    self.assertEqual(digest_hash, expected_digest_hash)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=12,
        location='/a_directory', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    with self.assertRaises(IOError):
      test_tool._CalculateDigestHash(file_entry, '')

  # TODO: add tests for _CreateSanitizedDestination.
  # TODO: add tests for _Extract.

  def testExtractDataStream(self):
    """Tests the _ExtractDataStream function."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool()

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location='/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    with shared_test_lib.TempDirectory() as temp_directory:
      test_tool._ExtractDataStream(
          file_entry, '', temp_directory, output_writer)

  def testExtractFileEntry(self):
    """Tests the _ExtractFileEntry function."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool()

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location='/a_directory/another_file', parent=os_path_spec)

    non_existent_test_path = self._GetTestFilePath(['does_not_exist'])
    non_existent_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=non_existent_test_path)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_tool._ExtractFileEntry(
          tsk_path_spec, temp_directory, output_writer)
      test_tool._ExtractFileEntry(
          non_existent_path_spec, temp_directory, output_writer)

  # TODO: add tests for _ExtractWithFilter.
  # TODO: add tests for _GetSourceFileSystem.

  def testParseExtensionsString(self):
    """Tests the _ParseExtensionsString function."""
    test_tool = image_export_tool.ImageExportTool()

    test_tool._ParseExtensionsString('txt')

  # TODO: add tests for _ParseFilterOptions.

  def testParseNamesString(self):
    """Tests the _ParseNamesString function."""
    test_tool = image_export_tool.ImageExportTool()

    test_tool._ParseNamesString('another_file')

  def testParseSignatureIdentifiers(self):
    """Tests the _ParseSignatureIdentifiers function."""
    test_tool = image_export_tool.ImageExportTool()

    test_tool._ParseSignatureIdentifiers(self._DATA_PATH, 'gzip')

    with self.assertRaises(ValueError):
      test_tool._ParseSignatureIdentifiers(None, 'gzip')

    with self.assertRaises(IOError):
      test_path = os.path.join(os.sep, 'bogus')
      test_tool._ParseSignatureIdentifiers(test_path, 'gzip')

  # TODO: add tests for _Preprocess.
  # TODO: add tests for _ReadSpecificationFile.

  def testWriteFileEntry(self):
    """Tests the _WriteFileEntry function."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    test_tool = image_export_tool.ImageExportTool()

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location='/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    with shared_test_lib.TempDirectory() as temp_directory:
      destination_path = os.path.join(temp_directory, 'another_file')
      test_tool._WriteFileEntry(file_entry, '', destination_path)

  # TODO: add tests for AddFilterOptions.

  def testListSignatureIdentifiers(self):
    """Tests the ListSignatureIdentifiers function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    test_tool._data_location = self._TEST_DATA_PATH

    test_tool.ListSignatureIdentifiers()

    expected_output = (
        'Available signature identifiers:\n'
        '7z, bzip2, esedb, evt, evtx, ewf_e01, ewf_l01, exe_mz, gzip, lnk, '
        'msiecf, nk2,\n'
        'olecf, olecf_beta, pdf, pff, qcow, rar, regf, tar, tar_old, '
        'vhdi_footer,\n'
        'vhdi_header, wtcdb_cache, wtcdb_index, zip\n'
        '\n')

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output.split('\n'))

    test_tool._data_location = self._GetTestFilePath(['tmp'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ListSignatureIdentifiers()

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    result = test_tool.ParseArguments([])
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['image.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.image = test_file_path

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  def testPrintFilterCollection(self):
    """Tests the PrintFilterCollection function."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['image.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.date_filters = ['ctime,2012-05-25 15:59:00,2012-05-25 15:59:20']
    options.image = test_file_path
    options.quiet = True

    test_tool.ParseOptions(options)

    test_tool.PrintFilterCollection()

    expected_output = '\n'.join([
        'Filters:',
        ('\tctime between 2012-05-25 15:59:00.000000 and '
         '2012-05-25 15:59:20.000000'),
        ''])
    output = output_writer.ReadOutput()
    self.assertEqual(output, expected_output)

  def testProcessSourcesWithImage(self):
    """Tests the ProcessSources function on a single partition image."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.image = self._GetTestFilePath(['ímynd.dd'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_output = '\n'.join([
          'Export started.',
          'Extracting file entries.',
          'Export completed.',
          '',
          ''])

      output = output_writer.ReadOutput()
      self.assertEqual(output, expected_output)

  def testProcessSourcesExtractWithDateTimeFilter(self):
    """Tests the ProcessSources function with a date time filter."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['image.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.date_filters = ['ctime,2012-05-25 15:59:00,2012-05-25 15:59:20']
    options.image = test_file_path
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, 'a_directory'),
          os.path.join(temp_directory, 'a_directory', 'a_file')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithExtensionsFilter(self):
    """Tests the ProcessSources function with an extensions filter."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['image.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.extensions_string = 'txt'
    options.image = test_file_path
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, 'passwords.txt')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithNamesFilter(self):
    """Tests the ProcessSources function with a names filter."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['image.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.image = test_file_path
    options.names_string = 'another_file'
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, 'a_directory'),
          os.path.join(temp_directory, 'a_directory', 'another_file')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithFilter(self):
    """Tests the ProcessSources function with a filter file."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['image.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.image = test_file_path
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      filter_file = os.path.join(temp_directory, 'filter.txt')
      with io.open(filter_file, 'wt', encoding='utf-8') as file_object:
        file_object.write('/a_directory/.+_file\n')

      options.file_filter = filter_file
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, 'filter.txt'),
          os.path.join(temp_directory, 'a_directory'),
          os.path.join(temp_directory, 'a_directory', 'another_file'),
          os.path.join(temp_directory, 'a_directory', 'a_file')])

      extracted_files = self._RecursiveList(temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithArtifactsFilter(self):
    """Tests the ProcessSources function with a artifacts filter file."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['image.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.image = test_file_path
    options.quiet = True
    options.artifact_filter_string = 'TestFilesImageExport'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, 'a_directory'),
          os.path.join(temp_directory, 'a_directory', 'another_file'),
          os.path.join(temp_directory, 'a_directory', 'a_file')])

      extracted_files = self._RecursiveList(temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithArtifactsGroupFilter(self):
    """Tests the ProcessSources function with a group artifacts filter file."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['image.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.image = test_file_path
    options.quiet = True
    options.artifact_filter_string = 'TestGroupExport'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, 'a_directory'),
          os.path.join(temp_directory, 'a_directory', 'another_file'),
          os.path.join(temp_directory, 'a_directory', 'a_file'),
          os.path.join(temp_directory, 'passwords.txt')])

      extracted_files = self._RecursiveList(temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithSignaturesFilter(self):
    """Tests the ProcessSources function with a signatures filter."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['syslog_image.dd'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.artifact_definitions_path = test_artifacts_path
    options.image = test_file_path
    options.quiet = True
    options.signature_identifiers = 'gzip'

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_extracted_files = sorted([
          os.path.join(temp_directory, 'logs'),
          os.path.join(temp_directory, 'logs', 'sys.tgz')])

      extracted_files = self._RecursiveList(temp_directory)
      self.assertEqual(sorted(extracted_files), expected_extracted_files)


if __name__ == '__main__':
  unittest.main()
