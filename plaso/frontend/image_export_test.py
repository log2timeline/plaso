#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the image export front-end."""

import glob
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


class Log2TimelineFrontendTest(test_lib.FrontendTestCase):
  """Tests for the image export front-end."""

  def setUp(self):
    """Sets up the objects used throughout the test."""
    self._temp_directory = tempfile.mkdtemp()

  def tearDown(self):
    """Cleans up the objects used throughout the test."""
    shutil.rmtree(self._temp_directory, True)

  def testProcessSourceExtractWithDateFilter(self):
    """Tests extract with file filter and date filter functionality."""
    test_front_end = image_export.ImageExportFrontend()

    options = frontend.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory
    options.include_duplicates = True

    options.filter = os.path.join(self._temp_directory, u'filter.txt')
    with open(options.filter, 'wb') as file_object:
      file_object.write(b'/a_directory/.+_file\n')

    options.date_filters = [u'ctime, 2012-05-25 15:59:00, 2012-05-25 15:59:20']

    test_front_end.ParseOptions(options, source_option=u'image')
    test_front_end.PrintFilterCollection()

    test_front_end.ProcessSource(options)

    expected_text_files = sorted([
        os.path.join(self._temp_directory, u'a_directory', u'a_file')])

    text_files = glob.glob(os.path.join(
        self._temp_directory, u'a_directory', u'*'))

    self.assertEquals(sorted(text_files), expected_text_files)

    # We need to reset the date filter to not affect other tests.
    # pylint: disable=protected-access
    # TODO: Remove this once filtering has been moved to the front end object.
    image_export.FileSaver._date_filter = None

  def testProcessSourceExtractWithExtensions(self):
    """Tests extract with extensions process source functionality."""
    test_front_end = image_export.ImageExportFrontend()

    options = frontend.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory
    options.extension_string = u'txt'

    test_front_end.ParseOptions(options, source_option=u'image')

    test_front_end.ProcessSource(options)

    expected_text_files = sorted([
        os.path.join(self._temp_directory, u'passwords.txt')])

    text_files = glob.glob(os.path.join(self._temp_directory, u'*'))

    self.assertEquals(sorted(text_files), expected_text_files)

  def testProcessSourceExtractWithFilter(self):
    """Tests extract with filter process source functionality."""
    test_front_end = image_export.ImageExportFrontend()

    options = frontend.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory

    options.filter = os.path.join(self._temp_directory, u'filter.txt')
    with open(options.filter, 'wb') as file_object:
      file_object.write(b'/a_directory/.+_file\n')

    test_front_end.ParseOptions(options, source_option=u'image')

    test_front_end.ProcessSource(options)

    expected_text_files = sorted([
        os.path.join(self._temp_directory, u'a_directory', u'another_file'),
        os.path.join(self._temp_directory, u'a_directory', u'a_file')])

    text_files = glob.glob(os.path.join(
        self._temp_directory, u'a_directory', u'*'))

    self.assertEquals(sorted(text_files), expected_text_files)

  def testDateTimeFileEntryFilter(self):
    """Test the save file based on date filter function."""
    # Open up a file entry.
    path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=16,
        location=u'/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

    # Timestamps of file:
    #   Modified: 2012-05-25T15:59:23+00:00
    #   Accessed: 2012-05-25T15:59:23+00:00
    #    Created: 2012-05-25T15:59:23+00:00

    date_filter = image_export.DateTimeFileEntryFilter()

    self.assertTrue(date_filter.Matches(file_entry))

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

    # Testing adding a badly formatter filter.
    with self.assertRaises(ValueError):
      date_filter.AddDateTimeRange(
          u'foobar', start_time_string=u'2012-02-01 01:01:01')

    # Testing adding a badly formatter filter, no date set.
    date_filter = image_export.DateTimeFileEntryFilter()
    with self.assertRaises(ValueError):
      date_filter.AddDateTimeRange(u'atime')

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
    self.assertEquals(len(date_filter._date_time_ranges), 3)


if __name__ == '__main__':
  unittest.main()
