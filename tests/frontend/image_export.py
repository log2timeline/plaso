#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the image export front-end."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.frontend import image_export
from plaso.lib import specification

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib
from tests.frontend import test_lib


class DateTimeFileEntryFilterTest(shared_test_lib.BaseTestCase):
  """Tests the date time file entry filter."""

  # pylint: disable=protected-access

  def testAddDateTimeRange(self):
    """Tests the AddDateTimeRange function."""
    test_filter = image_export.DateTimeFileEntryFilter()

    test_filter.AddDateTimeRange(
        u'ctime', end_time_string=u'2012-05-25 15:59:25',
        start_time_string=u'2012-05-25 15:59:20')

    with self.assertRaises(ValueError):
      test_filter.AddDateTimeRange(None)

    # Testing adding a badly formatter filter.
    with self.assertRaises(ValueError):
      test_filter.AddDateTimeRange(
          u'foobar', start_time_string=u'2012-02-01 01:01:01')

    with self.assertRaises(ValueError):
      test_filter.AddDateTimeRange(
          u'ctime', end_time_string=u'2012-05-25 15:59:20',
          start_time_string=u'2012-05-25 15:59:25')

    # Testing adding a badly formatter filter, no date set.
    with self.assertRaises(ValueError):
      test_filter.AddDateTimeRange(u'atime')

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testMatches(self):
    """Tests the Matches function."""
    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

    # Timestamps of file:
    #   Modified: 2012-05-25T15:59:23+00:00
    #   Accessed: 2012-05-25T15:59:23+00:00
    #    Created: 2012-05-25T15:59:23+00:00

    test_filter = image_export.DateTimeFileEntryFilter()

    # When no date time ranges are specified the filter returns None.
    self.assertIsNone(test_filter.Matches(file_entry))

    # Add a date to the date filter.
    test_filter.AddDateTimeRange(
        u'ctime', start_time_string=u'2012-05-25 15:59:20',
        end_time_string=u'2012-05-25 15:59:25')
    self.assertTrue(test_filter.Matches(file_entry))

    test_filter = image_export.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        u'ctime', start_time_string=u'2012-05-25 15:59:24',
        end_time_string=u'2012-05-25 15:59:55')
    self.assertFalse(test_filter.Matches(file_entry))

    # Testing a timestamp that does not exist in the stat object.
    test_filter = image_export.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        u'bkup', start_time_string=u'2012-02-02 12:12:12')
    self.assertTrue(test_filter.Matches(file_entry))

    # Just end date set.
    test_filter = image_export.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        u'mtime', end_time_string=u'2012-05-25 15:59:55')
    self.assertTrue(test_filter.Matches(file_entry))

    # Just with a start date but within range.
    test_filter = image_export.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        u'atime', start_time_string=u'2012-03-25 15:59:55')
    self.assertTrue(test_filter.Matches(file_entry))

    # And now with a start date, but out of range.
    test_filter = image_export.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        u'ctime', start_time_string=u'2012-05-25 15:59:55')
    self.assertFalse(test_filter.Matches(file_entry))

    # Test with more than one date filter.
    test_filter = image_export.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        u'ctime', start_time_string=u'2012-05-25 15:59:55',
        end_time_string=u'2012-05-25 17:34:12')
    test_filter.AddDateTimeRange(
        u'atime', start_time_string=u'2012-05-25 15:59:20',
        end_time_string=u'2012-05-25 15:59:25')
    test_filter.AddDateTimeRange(
        u'mtime', start_time_string=u'2012-05-25 15:59:24',
        end_time_string=u'2012-05-25 15:59:55')

    self.assertFalse(test_filter.Matches(file_entry))
    self.assertEqual(len(test_filter._date_time_ranges), 3)

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_filter = image_export.DateTimeFileEntryFilter()

    test_filter.AddDateTimeRange(
        u'ctime', end_time_string=u'2012-05-25 15:59:25',
        start_time_string=u'2012-05-25 15:59:20')

    test_filter.AddDateTimeRange(
        u'atime', end_time_string=u'2012-05-25 15:59:25')

    test_filter.AddDateTimeRange(
        u'mtime', start_time_string=u'2012-05-25 15:59:20')

    test_filter.Print(output_writer)

    expected_output = [
        (b'\tctime between 2012-05-25T15:59:20+00:00 and '
         b'2012-05-25T15:59:25+00:00'),
        b'\tatime after 2012-05-25T15:59:25+00:00',
        b'\tmtime before 2012-05-25T15:59:20+00:00',
        b'']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output)


class ExtensionsFileEntryFilterTest(shared_test_lib.BaseTestCase):
  """Tests the extensions file entry filter."""

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testMatches(self):
    """Tests the Matches function."""
    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    test_filter = image_export.ExtensionsFileEntryFilter([u'txt'])

    # Test a filter match.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
        location=u'/passwords.txt', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertTrue(test_filter.Matches(file_entry))

    # Test a filter non-match.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

    # Test that fails because path specification has no location.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15, parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_filter = image_export.ExtensionsFileEntryFilter([u'exe', u'pdf'])

    test_filter.Print(output_writer)

    expected_output = [
        b'\textensions: exe, pdf',
        b'']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output)


class NamesFileEntryFilterTest(shared_test_lib.BaseTestCase):
  """Tests the names file entry filter."""

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testMatches(self):
    """Tests the Matches function."""
    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    test_filter = image_export.NamesFileEntryFilter([u'passwords.txt'])

    # Test a filter non-match.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

    # Test a filter on a directory.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=12,
        location=u'/a_directory', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

    # Test a filter match.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
        location=u'/passwords.txt', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertTrue(test_filter.Matches(file_entry))

    # Test a filter without names.
    test_filter = image_export.NamesFileEntryFilter([])
    self.assertFalse(test_filter.Matches(file_entry))

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_filter = image_export.NamesFileEntryFilter([u'myfile'])

    test_filter.Print(output_writer)

    expected_output = [
        b'\tnames: myfile',
        b'']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output)


class SignaturesFileEntryFilterTest(shared_test_lib.BaseTestCase):
  """Tests the signatures file entry filter."""

  # pylint: disable=protected-access

  def testGetScanner(self):
    """Tests the _GetScanner function."""
    test_filter = image_export.SignaturesFileEntryFilter(None, [])

    test_filter._GetScanner(None, [])
    self.assertIsNone(test_filter._file_scanner)

    specification_store = specification.FormatSpecificationStore()
    format_specification = specification.FormatSpecification(u'no_offset')
    format_specification.AddNewSignature(b'test1')
    specification_store.AddSpecification(format_specification)

    format_specification = specification.FormatSpecification(u'negative_offset')
    format_specification.AddNewSignature(b'test2', offset=-4)
    specification_store.AddSpecification(format_specification)

    format_specification = specification.FormatSpecification(u'positive_offset')
    format_specification.AddNewSignature(b'test3', offset=4)
    specification_store.AddSpecification(format_specification)

    with self.assertRaises(TypeError):
      # Currently pysigscan does not support patterns without an offset.
      test_filter._GetScanner(specification_store, [u'no_offset'])

    file_scanner = test_filter._GetScanner(
        specification_store, [u'negative_offset'])
    self.assertIsNotNone(file_scanner)

    file_scanner = test_filter._GetScanner(
        specification_store, [u'positive_offset'])
    self.assertIsNotNone(file_scanner)

  @shared_test_lib.skipUnlessHasTestFile([u'NTUSER.DAT'])
  @shared_test_lib.skipUnlessHasTestFile([u'test_pe.exe'])
  def testMatches(self):
    """Tests the Matches function."""
    specification_store = specification.FormatSpecificationStore()
    format_specification = specification.FormatSpecification(u'regf')
    format_specification.AddNewSignature(b'regf', offset=0)
    specification_store.AddSpecification(format_specification)

    test_filter = image_export.SignaturesFileEntryFilter(
        specification_store, [u'regf'])

    # Test a filter match.
    test_path = self._GetTestFilePath([u'NTUSER.DAT'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    self.assertTrue(test_filter.Matches(file_entry))

    # Test a filter non-match.
    test_path = self._GetTestFilePath([u'test_pe.exe'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')

    specification_store = specification.FormatSpecificationStore()
    specification_store.AddNewSpecification(u'7z')

    test_filter = image_export.SignaturesFileEntryFilter(
        specification_store, [u'7z', u'bzip2'])

    test_filter.Print(output_writer)

    expected_output = [
        b'\tsignature identifiers: 7z',
        b'']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output)


class FileEntryFilterCollectionTest(shared_test_lib.BaseTestCase):
  """Tests the file entry filter collection."""

  # pylint: disable=protected-access

  def testAddFilter(self):
    """Tests the AddFilter function."""
    test_filter_collection = image_export.FileEntryFilterCollection()

    self.assertEqual(len(test_filter_collection._filters), 0)

    file_entry_filter = image_export.NamesFileEntryFilter([u'name'])
    test_filter_collection.AddFilter(file_entry_filter)
    self.assertEqual(len(test_filter_collection._filters), 1)

  def testHasFilters(self):
    """Tests the HasFilters function."""
    test_filter_collection = image_export.FileEntryFilterCollection()
    self.assertFalse(test_filter_collection.HasFilters())

    test_filter_collection = image_export.FileEntryFilterCollection()
    file_entry_filter = image_export.NamesFileEntryFilter([u'name'])
    test_filter_collection.AddFilter(file_entry_filter)
    self.assertTrue(test_filter_collection.HasFilters())

  # TODO: add test for Matches.
  # TODO: add test for Print.


class ImageExportFrontendTest(shared_test_lib.BaseTestCase):
  """Tests the image export front-end."""

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
    test_front_end = image_export.ImageExportFrontend()

    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    digest_hash = test_front_end._CalculateDigestHash(file_entry, u'')
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
      test_front_end._CalculateDigestHash(file_entry, u'')

  # TODO: add test for _CreateSanitizedDestinationDirectory.
  # TODO: add test for _Extract.

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testExtractDataStream(self):
    """Tests the _ExtractDataStream function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_front_end = image_export.ImageExportFrontend()

    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    with shared_test_lib.TempDirectory() as temp_directory:
      test_front_end._ExtractDataStream(
          file_entry, u'', temp_directory, output_writer)

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testExtractFileEntry(self):
    """Tests the _ExtractFileEntry function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_front_end = image_export.ImageExportFrontend()

    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_front_end._ExtractFileEntry(
          tsk_path_spec, temp_directory, output_writer)

  # TODO: add test for _ExtractWithFilter.
  # TODO: add test for _GetSourceFileSystem.
  # TODO: add test for _Preprocess.

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testWriteFileEntry(self):
    """Tests the _WriteFileEntry function."""
    test_front_end = image_export.ImageExportFrontend()

    test_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    with shared_test_lib.TempDirectory() as temp_directory:
      destination_path = os.path.join(temp_directory, u'another_file')
      test_front_end._WriteFileEntry(file_entry, u'', destination_path)

  def testHasFilters(self):
    """Tests the HasFilters function."""
    test_front_end = image_export.ImageExportFrontend()
    self.assertFalse(test_front_end.HasFilters())

    test_front_end = image_export.ImageExportFrontend()
    test_front_end.ParseDateFilters([
        u'ctime, 2012-05-25 15:59:00, 2012-05-25 15:59:20'])
    self.assertTrue(test_front_end.HasFilters())

    test_front_end = image_export.ImageExportFrontend()
    test_front_end.ParseExtensionsString(u'txt')
    self.assertTrue(test_front_end.HasFilters())

    test_front_end = image_export.ImageExportFrontend()
    test_front_end.ParseNamesString(u'another_file')
    self.assertTrue(test_front_end.HasFilters())

    test_front_end = image_export.ImageExportFrontend()
    test_front_end.ParseSignatureIdentifiers(self._DATA_PATH, u'gzip')
    self.assertTrue(test_front_end.HasFilters())

  def testParseDateFilters(self):
    """Tests the ParseDateFilters function."""
    test_front_end = image_export.ImageExportFrontend()

    test_front_end.ParseDateFilters([
        u'ctime, 2012-05-25 15:59:00, 2012-05-25 15:59:20'])

    with self.assertRaises(ValueError):
      test_front_end.ParseDateFilters([u'ctime, 2012-05-25 15:59:00'])

    with self.assertRaises(ValueError):
      test_front_end.ParseDateFilters([
          u'ctime, 2012-05-25 15:59:00, 2012-05-A5 15:59:20'])

  def testParseExtensionsString(self):
    """Tests the ParseExtensionsString function."""
    test_front_end = image_export.ImageExportFrontend()

    test_front_end.ParseExtensionsString(u'txt')

  def testParseNamesString(self):
    """Tests the ParseNamesString function."""
    test_front_end = image_export.ImageExportFrontend()

    test_front_end.ParseNamesString(u'another_file')

  def testParseSignatureIdentifiers(self):
    """Tests the ParseSignatureIdentifiers function."""
    test_front_end = image_export.ImageExportFrontend()

    test_front_end.ParseSignatureIdentifiers(self._DATA_PATH, u'gzip')

    with self.assertRaises(ValueError):
      test_front_end.ParseSignatureIdentifiers(None, u'gzip')

    with self.assertRaises(IOError):
      test_path = os.path.join(os.sep, u'bogus')
      test_front_end.ParseSignatureIdentifiers(test_path, u'gzip')

  # TODO: add test for PrintFilterCollection.

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithDateTimeFilter(self):
    """Tests the ProcessSources function with a date time filter."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_front_end = image_export.ImageExportFrontend()
    test_front_end.ParseDateFilters([
        u'ctime, 2012-05-25 15:59:00, 2012-05-25 15:59:20'])

    # TODO: move to corresponding CLI test.
    output_writer = test_lib.StringIOOutputWriter()
    test_front_end.PrintFilterCollection(output_writer)

    expected_value = (
        u'Filters:\n'
        u'\tctime between 2012-05-25T15:59:00+00:00 and '
        u'2012-05-25T15:59:20+00:00\n')
    value = output_writer.GetValue()
    self.assertEqual(value, expected_value)

    test_path = self._GetTestFilePath([u'image.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=qcow_path_spec)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_front_end.ProcessSources([path_spec], temp_directory, output_writer)

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'a_directory'),
          os.path.join(temp_directory, u'a_directory', u'a_file')])

      extracted_files = self._RecursiveList(temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithExtensionsFilter(self):
    """Tests the ProcessSources function with an extensions filter."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_front_end = image_export.ImageExportFrontend()
    test_front_end.ParseExtensionsString(u'txt')

    test_path = self._GetTestFilePath([u'image.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=qcow_path_spec)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_front_end.ProcessSources([path_spec], temp_directory, output_writer)

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'passwords.txt')])

      extracted_files = self._RecursiveList(temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithNamesFilter(self):
    """Tests the ProcessSources function with a names filter."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_front_end = image_export.ImageExportFrontend()
    test_front_end.ParseNamesString(u'another_file')

    test_path = self._GetTestFilePath([u'image.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=qcow_path_spec)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_front_end.ProcessSources([path_spec], temp_directory, output_writer)

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'a_directory'),
          os.path.join(temp_directory, u'a_directory', u'another_file')])

      extracted_files = self._RecursiveList(temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  @shared_test_lib.skipUnlessHasTestFile([u'image.qcow2'])
  def testProcessSourcesExtractWithFilter(self):
    """Tests the ProcessSources function with a filter file."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_front_end = image_export.ImageExportFrontend()

    test_path = self._GetTestFilePath([u'image.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=qcow_path_spec)

    with shared_test_lib.TempDirectory() as temp_directory:
      filter_file = os.path.join(temp_directory, u'filter.txt')
      with open(filter_file, 'wb') as file_object:
        file_object.write(b'/a_directory/.+_file\n')

      test_front_end.ProcessSources(
          [path_spec], temp_directory, output_writer, filter_file=filter_file)

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
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_front_end = image_export.ImageExportFrontend()
    test_front_end.ParseSignatureIdentifiers(self._DATA_PATH, u'gzip')

    test_path = self._GetTestFilePath([u'syslog_image.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_front_end.ProcessSources([path_spec], temp_directory, output_writer)

      expected_extracted_files = sorted([
          os.path.join(temp_directory, u'logs'),
          os.path.join(temp_directory, u'logs', u'sys.tgz')])

      extracted_files = self._RecursiveList(temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  # TODO: add test with remove duplicates disabled.
  # TODO: add test for ReadSpecificationFile.


if __name__ == '__main__':
  unittest.main()
