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

from tests.frontend import test_lib


class DateTimeFileEntryFilter(test_lib.FrontendTestCase):
  """Tests for the date time file entry filter."""

  def testAddDateTimeRange(self):
    """Tests the AddDateTimeRange function."""
    date_filter = image_export.DateTimeFileEntryFilter()

    date_filter.AddDateTimeRange(
        u'ctime', start_time_string=u'2012-05-25 15:59:20',
        end_time_string=u'2012-05-25 15:59:25')

    # Testing adding a badly formatter filter.
    with self.assertRaises(ValueError):
      date_filter.AddDateTimeRange(
          u'foobar', start_time_string=u'2012-02-01 01:01:01')

    # Testing adding a badly formatter filter, no date set.
    with self.assertRaises(ValueError):
      date_filter.AddDateTimeRange(u'atime')

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

    date_filter = image_export.DateTimeFileEntryFilter()

    # When no date time ranges are specified the filter returns None.
    self.assertIsNone(date_filter.Matches(file_entry))

    # Add a date to the date filter.
    date_filter.AddDateTimeRange(
        u'ctime', start_time_string=u'2012-05-25 15:59:20',
        end_time_string=u'2012-05-25 15:59:25')
    self.assertTrue(date_filter.Matches(file_entry))

    date_filter = image_export.DateTimeFileEntryFilter()
    date_filter.AddDateTimeRange(
        u'ctime', start_time_string=u'2012-05-25 15:59:24',
        end_time_string=u'2012-05-25 15:59:55')
    self.assertFalse(date_filter.Matches(file_entry))

    # Testing a timestamp that does not exist in the stat object.
    date_filter = image_export.DateTimeFileEntryFilter()
    date_filter.AddDateTimeRange(
        u'bkup', start_time_string=u'2012-02-02 12:12:12')
    self.assertTrue(date_filter.Matches(file_entry))

    # Just end date set.
    date_filter = image_export.DateTimeFileEntryFilter()
    date_filter.AddDateTimeRange(
        u'mtime', end_time_string=u'2012-05-25 15:59:55')
    self.assertTrue(date_filter.Matches(file_entry))

    # Just with a start date but within range.
    date_filter = image_export.DateTimeFileEntryFilter()
    date_filter.AddDateTimeRange(
        u'atime', start_time_string=u'2012-03-25 15:59:55')
    self.assertTrue(date_filter.Matches(file_entry))

    # And now with a start date, but out of range.
    date_filter = image_export.DateTimeFileEntryFilter()
    date_filter.AddDateTimeRange(
        u'ctime', start_time_string=u'2012-05-25 15:59:55')
    self.assertFalse(date_filter.Matches(file_entry))

    # Test with more than one date filter.
    date_filter = image_export.DateTimeFileEntryFilter()
    date_filter.AddDateTimeRange(
        u'ctime', start_time_string=u'2012-05-25 15:59:55',
        end_time_string=u'2012-05-25 17:34:12')
    date_filter.AddDateTimeRange(
        u'atime', start_time_string=u'2012-05-25 15:59:20',
        end_time_string=u'2012-05-25 15:59:25')
    date_filter.AddDateTimeRange(
        u'mtime', start_time_string=u'2012-05-25 15:59:24',
        end_time_string=u'2012-05-25 15:59:55')

    self.assertFalse(date_filter.Matches(file_entry))
    # pylint: disable=protected-access
    self.assertEqual(len(date_filter._date_time_ranges), 3)


class ImageExportFrontendTest(test_lib.FrontendTestCase):
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


if __name__ == '__main__':
  unittest.main()
