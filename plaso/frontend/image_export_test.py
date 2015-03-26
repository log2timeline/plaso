#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the image export front-end."""

import os
import shutil
import tempfile
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.frontend import frontend
from plaso.frontend import image_export
from plaso.frontend import test_lib


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
        definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

    # Timestamps of file:
    #   Modified: 2012-05-25T15:59:23+00:00
    #   Accessed: 2012-05-25T15:59:23+00:00
    #    Created: 2012-05-25T15:59:23+00:00

    date_filter = image_export.DateTimeFileEntryFilter()

    # When no date time ranges are specified the filter returns None.
    self.assertEqual(date_filter.Matches(file_entry), None)

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
    """Sets up the objects used by an individual test."""
    self._temp_directory = tempfile.mkdtemp()

    # TODO: do not use a class attribute here.
    # We need to flush the MD5 dict in FileSaver before each test.
    image_export.FileSaver.md5_dict = {}

  def tearDown(self):
    """Cleans up the objects used an individual test."""
    shutil.rmtree(self._temp_directory, True)
    self._temp_directory = None

  def testProcessSourceExtractWithDateTimeFilter(self):
    """Tests extract with a date time filter."""
    test_front_end = image_export.ImageExportFrontend()

    options = frontend.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory
    options.include_duplicates = True
    options.date_filters = [u'ctime, 2012-05-25 15:59:00, 2012-05-25 15:59:20']

    test_front_end.ParseOptions(options, source_option=u'image')
    test_front_end.PrintFilterCollection()

    test_front_end.ProcessSource(options)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'a_directory'),
        os.path.join(self._temp_directory, u'a_directory', u'a_file')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourceExtractWithExtensionsFilter(self):
    """Tests extract with an extensions filter."""
    test_front_end = image_export.ImageExportFrontend()

    options = frontend.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory
    options.extensions_string = u'txt'

    test_front_end.ParseOptions(options, source_option=u'image')

    test_front_end.ProcessSource(options)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'passwords.txt')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourceExtractWithNamesFilter(self):
    """Tests extract with a names filter."""
    test_front_end = image_export.ImageExportFrontend()

    options = frontend.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory
    options.names_string = u'another_file'

    test_front_end.ParseOptions(options, source_option=u'image')

    test_front_end.ProcessSource(options)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'a_directory'),
        os.path.join(self._temp_directory, u'a_directory', u'another_file')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourceExtractWithFilter(self):
    """Tests extract with a filter file."""
    test_front_end = image_export.ImageExportFrontend()

    options = frontend.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory

    options.filter = os.path.join(self._temp_directory, u'filter.txt')
    with open(options.filter, 'wb') as file_object:
      file_object.write(b'/a_directory/.+_file\n')

    test_front_end.ParseOptions(options, source_option=u'image')

    test_front_end.ProcessSource(options)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'filter.txt'),
        os.path.join(self._temp_directory, u'a_directory'),
        os.path.join(self._temp_directory, u'a_directory', u'another_file'),
        os.path.join(self._temp_directory, u'a_directory', u'a_file')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  def testProcessSourceExtractWithSignaturesFilter(self):
    """Tests extract with a signatures filter."""
    test_front_end = image_export.ImageExportFrontend()

    options = frontend.Options()
    options.image = self._GetTestFilePath([u'syslog_image.dd'])
    options.path = self._temp_directory
    options.data_location = self._DATA_PATH
    options.signature_identifiers = u'gzip'

    test_front_end.ParseOptions(options, source_option=u'image')

    test_front_end.ProcessSource(options)

    expected_extracted_files = sorted([
        os.path.join(self._temp_directory, u'logs'),
        os.path.join(self._temp_directory, u'logs', u'sys.tgz')])

    extracted_files = self._RecursiveList(self._temp_directory)

    self.assertEqual(sorted(extracted_files), expected_extracted_files)

  # TODO: add bogus data location test.


if __name__ == '__main__':
  unittest.main()
