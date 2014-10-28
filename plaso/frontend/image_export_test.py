#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the image export front-end."""

import glob
import os
import shutil
import tempfile
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.frontend import image_export
from plaso.frontend import test_lib
from plaso.lib import errors


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

    options = test_lib.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory
    options.include_duplicates = True

    options.filter = os.path.join(self._temp_directory, u'filter.txt')
    with open(options.filter, 'wb') as file_object:
      file_object.write('/a_directory/.+_file\n')

    test_front_end.ParseOptions(options, source_option='image')

    # Set the date filter.
    filter_start = '2012-05-25 15:59:00'
    filter_end = '2012-05-25 15:59:20'

    date_filter_object = image_export.DateFilter()
    date_filter_object.Add(
        filter_start=filter_start, filter_end=filter_end,
        filter_type='ctime')
    image_export.FileSaver.SetDateFilter(date_filter_object)

    test_front_end.ProcessSource(options)

    expected_text_files = sorted([
      os.path.join(self._temp_directory, u'a_directory', u'a_file')])

    text_files = glob.glob(os.path.join(
        self._temp_directory, u'a_directory', u'*'))

    self.assertEquals(sorted(text_files), expected_text_files)

    # We need to reset the date filter to not affect other tests.
    # pylint: disable-msg=protected-access
    # TODO: Remove this once filtering has been moved to the front end object.
    image_export.FileSaver._date_filter = None

  def testProcessSourceExtractWithExtensions(self):
    """Tests extract with extensions process source functionality."""
    test_front_end = image_export.ImageExportFrontend()

    options = test_lib.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory
    options.extension_string = u'txt'

    test_front_end.ParseOptions(options, source_option='image')

    test_front_end.ProcessSource(options)

    expected_text_files = sorted([
      os.path.join(self._temp_directory, u'passwords.txt')])

    text_files = glob.glob(os.path.join(self._temp_directory, u'*'))

    self.assertEquals(sorted(text_files), expected_text_files)

  def testProcessSourceExtractWithFilter(self):
    """Tests extract with filter process source functionality."""
    test_front_end = image_export.ImageExportFrontend()

    options = test_lib.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory

    options.filter = os.path.join(self._temp_directory, u'filter.txt')
    with open(options.filter, 'wb') as file_object:
      file_object.write('/a_directory/.+_file\n')

    test_front_end.ParseOptions(options, source_option='image')

    test_front_end.ProcessSource(options)

    expected_text_files = sorted([
      os.path.join(self._temp_directory, u'a_directory', u'another_file'),
      os.path.join(self._temp_directory, u'a_directory', u'a_file')])

    text_files = glob.glob(os.path.join(
        self._temp_directory, u'a_directory', u'*'))

    self.assertEquals(sorted(text_files), expected_text_files)

  def testDateFilter(self):
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

    # Create the date filter object.
    date_filter = image_export.DateFilter()

    # No date filter set
    self.assertTrue(
        date_filter.CompareFileEntry(file_entry))

    # Add a date to the date filter.
    date_filter.Add(
        filter_start='2012-05-25 15:59:20', filter_end='2012-05-25 15:59:25',
        filter_type='ctime')

    self.assertTrue(date_filter.CompareFileEntry(file_entry))
    date_filter.Reset()

    date_filter.Add(
        filter_start='2012-05-25 15:59:24', filter_end='2012-05-25 15:59:55',
        filter_type='ctime')
    self.assertFalse(date_filter.CompareFileEntry(file_entry))
    date_filter.Reset()

    # Testing a timestamp that does not exist in the stat object.
    date_filter.Add(filter_type='bkup', filter_start='2012-02-02 12:12:12')
    with self.assertRaises(errors.WrongFilterOption):
      date_filter.CompareFileEntry(file_entry)

    # Testing adding a badly formatter filter.
    with self.assertRaises(errors.WrongFilterOption):
      date_filter.Add(filter_type='foobar', filter_start='2012-02-01 01:01:01')
    date_filter.Reset()

    # Testing adding a badly formatter filter, no date set.
    with self.assertRaises(errors.WrongFilterOption):
      date_filter.Add(filter_type='atime')
    date_filter.Reset()

    # Just end date set.
    date_filter.Add(
        filter_end='2012-05-25 15:59:55', filter_type='mtime')
    self.assertTrue(date_filter.CompareFileEntry(file_entry))
    date_filter.Reset()

    # Just with a start date but within range.
    date_filter.Add(
        filter_start='2012-03-25 15:59:55', filter_type='atime')
    self.assertTrue(date_filter.CompareFileEntry(file_entry))
    date_filter.Reset()

    # And now with a start date, but out of range.
    date_filter.Add(
        filter_start='2012-05-25 15:59:55', filter_type='ctime')
    self.assertFalse(date_filter.CompareFileEntry(file_entry))
    date_filter.Reset()

    # Test with more than one date filter.
    date_filter.Add(
        filter_start='2012-05-25 15:59:55', filter_type='ctime',
        filter_end='2012-05-25 17:34:12')
    date_filter.Add(
        filter_start='2012-05-25 15:59:20', filter_end='2012-05-25 15:59:25',
        filter_type='atime')
    date_filter.Add(
        filter_start='2012-05-25 15:59:24', filter_end='2012-05-25 15:59:55',
        filter_type='mtime')
    self.assertFalse(date_filter.CompareFileEntry(file_entry))
    self.assertEquals(date_filter.number_of_filters, 3)
    # Remove a filter.
    date_filter.Remove(
        filter_start='2012-05-25 15:59:55', filter_type='ctime',
        filter_end='2012-05-25 17:34:12')
    self.assertEquals(date_filter.number_of_filters, 2)

    # Remove a date filter that does not exist.
    date_filter.Remove(
        filter_start='2012-05-25 11:59:55', filter_type='ctime',
        filter_end='2012-05-25 17:34:12')
    self.assertEquals(date_filter.number_of_filters, 2)

    date_filter.Add(
        filter_end='2012-05-25 15:59:25', filter_type='atime')
    self.assertEquals(date_filter.number_of_filters, 3)
    date_filter.Remove(
        filter_end='2012-05-25 15:59:25', filter_type='atime')
    self.assertEquals(date_filter.number_of_filters, 2)

    date_filter.Reset()


if __name__ == '__main__':
  unittest.main()
