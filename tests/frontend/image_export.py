#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the image export front-end."""

import os
import shutil
import tempfile
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
  """Tests for the date time file entry filter."""

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
  """Tests for the extensions file entry filter."""

  def testMatches(self):
    """Tests the Matches function."""
    # TODO: implement.

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_filter = image_export.ExtensionsFileEntryFilter([u'exe', u'pdf'])

    # TODO: implement.

    test_filter.Print(output_writer)

    expected_output = [
        b'\textensions: exe, pdf',
        b'']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output)


class NamesFileEntryFilterTest(shared_test_lib.BaseTestCase):
  """Tests for the names file entry filter."""

  def testMatches(self):
    """Tests the Matches function."""
    # TODO: implement.

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_filter = image_export.NamesFileEntryFilter([u'myfile'])

    # TODO: implement.

    test_filter.Print(output_writer)

    expected_output = [
        b'\tnames: myfile',
        b'']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output)


class SignaturesFileEntryFilterTest(shared_test_lib.BaseTestCase):
  """Tests for the signatures file entry filter."""

  # TODO: add test for _GetScanner.

  def testMatches(self):
    """Tests the Matches function."""
    # TODO: implement.

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    sepcification_store = specification.FormatSpecificationStore()
    sepcification_store.AddNewSpecification(u'7z')
    test_filter = image_export.SignaturesFileEntryFilter(
        sepcification_store, [u'7z', u'bzip2'])

    # TODO: implement.

    test_filter.Print(output_writer)

    expected_output = [
        b'\tsignature identifiers: 7z',
        b'']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output)


# TODO: add tests for FileEntryFilterCollection.
# TODO: add tests for FileSaver.


class ImageExportFrontendTest(shared_test_lib.BaseTestCase):
  """Tests for the image export front-end."""

  def _RecursiveList(self, path):
    """Recursively lists a file or directory.

    Args:
      path: the path of the file or directory to list.

    Returns:
      A list of files and sub directories within the path.
    """
    results = []
    for sub_path, _, files in os.walk(path):
      if sub_path != path:
        results.append(sub_path)

      for file_entry in files:
        results.append(os.path.join(sub_path, file_entry))

    return results

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._temp_directory = tempfile.mkdtemp()

    # TODO: do not use a class attribute here.
    # We need to flush the MD5 dict in FileSaver before each test.
    image_export.FileSaver.md5_dict = {}

  def tearDown(self):
    """Cleans up after running an individual test."""
    shutil.rmtree(self._temp_directory, True)
    self._temp_directory = None

  def _GetTestScanNode(self, scan_context):
    """Retrieves the scan node for testing.

    Retrieves the first scan node, from the root upwards, with more or less
    than 1 sub node.

    Args:
      scan_context: scan context (instance of dfvfs.ScanContext).

    Returns:
      A scan node (instance of dfvfs.ScanNode).
    """
    scan_node = scan_context.GetRootScanNode()
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    return scan_node

  # TODO: add test for _Extract.
  # TODO: add test for _ExtractFile.
  # TODO: add test for _ExtractWithFilter.
  # TODO: add test for _GetSourceFileSystem.
  # TODO: add test for _Preprocess.
  # TODO: add test for HasFilters.
  # TODO: add test for ParseDateFilters.
  # TODO: add test for ParseExtensionsString.
  # TODO: add test for ParseNamesString.
  # TODO: add test for ParseSignatureIdentifiers.
  # TODO: add test for PrintFilterCollection.

  def testProcessSourcesExtractWithDateTimeFilter(self):
    """Tests the ProcessSources function with a date time filter."""
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

    test_front_end.ProcessSources([path_spec], self._temp_directory)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'a_directory'),
        os.path.join(self._temp_directory, u'a_directory', u'a_file')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithExtensionsFilter(self):
    """Tests the ProcessSources function with an extensions filter."""
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

    test_front_end.ProcessSources([path_spec], self._temp_directory)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'passwords.txt')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithNamesFilter(self):
    """Tests the ProcessSources function with a names filter."""
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

    test_front_end.ProcessSources([path_spec], self._temp_directory)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'a_directory'),
        os.path.join(self._temp_directory, u'a_directory', u'another_file')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithFilter(self):
    """Tests the ProcessSources function with a filter file."""
    test_front_end = image_export.ImageExportFrontend()

    filter_file = os.path.join(self._temp_directory, u'filter.txt')
    with open(filter_file, 'wb') as file_object:
      file_object.write(b'/a_directory/.+_file\n')

    test_path = self._GetTestFilePath([u'image.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=qcow_path_spec)

    test_front_end.ProcessSources(
        [path_spec], self._temp_directory, filter_file=filter_file)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'filter.txt'),
        os.path.join(self._temp_directory, u'a_directory'),
        os.path.join(self._temp_directory, u'a_directory', u'another_file'),
        os.path.join(self._temp_directory, u'a_directory', u'a_file')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourcesExtractWithSignaturesFilter(self):
    """Tests the ProcessSources function with a signatures filter."""
    test_front_end = image_export.ImageExportFrontend()
    test_front_end.ParseSignatureIdentifiers(self._DATA_PATH, u'gzip')

    test_path = self._GetTestFilePath([u'syslog_image.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    test_front_end.ProcessSources([path_spec], self._temp_directory)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'logs'),
        os.path.join(self._temp_directory, u'logs', u'sys.tgz')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  # TODO: add test with remove duplicates disabled.
  # TODO: add test for ReadSpecificationFile.


if __name__ == '__main__':
  unittest.main()
