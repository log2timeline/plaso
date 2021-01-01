#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the file entry filters."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.filters import file_entry as file_entry_filters
from plaso.lib import specification

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib


class DateTimeFileEntryFilterTest(shared_test_lib.BaseTestCase):
  """Tests the date time file entry filter."""

  # pylint: disable=protected-access

  def testAddDateTimeRange(self):
    """Tests the AddDateTimeRange function."""
    test_filter = file_entry_filters.DateTimeFileEntryFilter()

    test_filter.AddDateTimeRange(
        'ctime', end_time_string='2012-05-25 15:59:25',
        start_time_string='2012-05-25 15:59:20')

    with self.assertRaises(ValueError):
      test_filter.AddDateTimeRange(None)

    # Testing adding a badly formatter filter.
    with self.assertRaises(ValueError):
      test_filter.AddDateTimeRange(
          'foobar', start_time_string='2012-02-01 01:01:01')

    with self.assertRaises(ValueError):
      test_filter.AddDateTimeRange(
          'ctime', end_time_string='2012-05-25 15:59:20',
          start_time_string='2012-05-25 15:59:25')

    # Testing adding a badly formatter filter, no date set.
    with self.assertRaises(ValueError):
      test_filter.AddDateTimeRange('atime')

  def testMatches(self):
    """Tests the Matches function."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location='/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

    # Timestamps of file:
    #   Modified: 2012-05-25T15:59:23+00:00
    #   Accessed: 2012-05-25T15:59:23+00:00
    #    Created: 2012-05-25T15:59:23+00:00

    test_filter = file_entry_filters.DateTimeFileEntryFilter()

    # When no date time ranges are specified the filter returns None.
    self.assertIsNone(test_filter.Matches(file_entry))

    # Add a date to the date filter.
    test_filter.AddDateTimeRange(
        'ctime', start_time_string='2012-05-25 15:59:20',
        end_time_string='2012-05-25 15:59:25')
    self.assertTrue(test_filter.Matches(file_entry))

    test_filter = file_entry_filters.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        'ctime', start_time_string='2012-05-25 15:59:24',
        end_time_string='2012-05-25 15:59:55')
    self.assertFalse(test_filter.Matches(file_entry))

    # Testing a timestamp that does not exist in the stat object.
    test_filter = file_entry_filters.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        'bkup', start_time_string='2012-02-02 12:12:12')
    self.assertTrue(test_filter.Matches(file_entry))

    # Just end date set.
    test_filter = file_entry_filters.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        'mtime', end_time_string='2012-05-25 15:59:55')
    self.assertTrue(test_filter.Matches(file_entry))

    # Just with a start date but within range.
    test_filter = file_entry_filters.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        'atime', start_time_string='2012-03-25 15:59:55')
    self.assertTrue(test_filter.Matches(file_entry))

    # And now with a start date, but out of range.
    test_filter = file_entry_filters.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        'ctime', start_time_string='2012-05-25 15:59:55')
    self.assertFalse(test_filter.Matches(file_entry))

    # Test with more than one date filter.
    test_filter = file_entry_filters.DateTimeFileEntryFilter()
    test_filter.AddDateTimeRange(
        'ctime', start_time_string='2012-05-25 15:59:55',
        end_time_string='2012-05-25 17:34:12')
    test_filter.AddDateTimeRange(
        'atime', start_time_string='2012-05-25 15:59:20',
        end_time_string='2012-05-25 15:59:25')
    test_filter.AddDateTimeRange(
        'mtime', start_time_string='2012-05-25 15:59:24',
        end_time_string='2012-05-25 15:59:55')

    self.assertFalse(test_filter.Matches(file_entry))
    self.assertEqual(len(test_filter._date_time_ranges), 3)

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestBinaryOutputWriter(encoding='utf-8')
    test_filter = file_entry_filters.DateTimeFileEntryFilter()

    test_filter.AddDateTimeRange(
        'ctime', end_time_string='2012-05-25 15:59:25',
        start_time_string='2012-05-25 15:59:20')

    test_filter.AddDateTimeRange(
        'atime', end_time_string='2012-05-25 15:59:25')

    test_filter.AddDateTimeRange(
        'mtime', start_time_string='2012-05-25 15:59:20')

    test_filter.Print(output_writer)

    expected_output = [
        (b'\tctime between 2012-05-25 15:59:20.000000 and '
         b'2012-05-25 15:59:25.000000'),
        b'\tatime after 2012-05-25 15:59:25.000000',
        b'\tmtime before 2012-05-25 15:59:20.000000',
        b'']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output)


class ExtensionsFileEntryFilterTest(shared_test_lib.BaseTestCase):
  """Tests the extensions file entry filter."""

  def testMatches(self):
    """Tests the Matches function."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    test_filter = file_entry_filters.ExtensionsFileEntryFilter(['txt'])

    # Test a filter match.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
        location='/passwords.txt', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertTrue(test_filter.Matches(file_entry))

    # Test a filter non-match.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location='/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

    # Test that fails because path specification has no location.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15, parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestBinaryOutputWriter(encoding='utf-8')
    test_filter = file_entry_filters.ExtensionsFileEntryFilter(['exe', 'pdf'])

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

  def testMatches(self):
    """Tests the Matches function."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    test_filter = file_entry_filters.NamesFileEntryFilter(['passwords.txt'])

    # Test a filter non-match.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=16,
        location='/a_directory/another_file', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

    # Test a filter on a directory.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=12,
        location='/a_directory', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

    # Test a filter match.
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
        location='/passwords.txt', parent=os_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
    self.assertTrue(test_filter.Matches(file_entry))

    # Test a filter without names.
    test_filter = file_entry_filters.NamesFileEntryFilter([])
    self.assertFalse(test_filter.Matches(file_entry))

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestBinaryOutputWriter(encoding='utf-8')
    test_filter = file_entry_filters.NamesFileEntryFilter(['myfile'])

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
    test_filter = file_entry_filters.SignaturesFileEntryFilter(None, [])

    test_filter._GetScanner(None, [])
    self.assertIsNone(test_filter._file_scanner)

    specification_store = specification.FormatSpecificationStore()
    format_specification = specification.FormatSpecification('no_offset')
    format_specification.AddNewSignature(b'test1')
    specification_store.AddSpecification(format_specification)

    format_specification = specification.FormatSpecification('negative_offset')
    format_specification.AddNewSignature(b'test2', offset=-4)
    specification_store.AddSpecification(format_specification)

    format_specification = specification.FormatSpecification('positive_offset')
    format_specification.AddNewSignature(b'test3', offset=4)
    specification_store.AddSpecification(format_specification)

    with self.assertRaises(TypeError):
      # Currently pysigscan does not support patterns without an offset.
      test_filter._GetScanner(specification_store, ['no_offset'])

    file_scanner = test_filter._GetScanner(
        specification_store, ['negative_offset'])
    self.assertIsNotNone(file_scanner)

    file_scanner = test_filter._GetScanner(
        specification_store, ['positive_offset'])
    self.assertIsNotNone(file_scanner)

  def testMatches(self):
    """Tests the Matches function."""
    specification_store = specification.FormatSpecificationStore()
    format_specification = specification.FormatSpecification('regf')
    format_specification.AddNewSignature(b'regf', offset=0)
    specification_store.AddSpecification(format_specification)

    test_filter = file_entry_filters.SignaturesFileEntryFilter(
        specification_store, ['regf'])

    # Test a filter match.
    test_file_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    self.assertTrue(test_filter.Matches(file_entry))

    # Test a filter non-match.
    test_file_path = self._GetTestFilePath(['test_pe.exe'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    self.assertFalse(test_filter.Matches(file_entry))

  def testPrint(self):
    """Tests the Print function."""
    output_writer = cli_test_lib.TestBinaryOutputWriter(encoding='utf-8')

    specification_store = specification.FormatSpecificationStore()
    specification_store.AddNewSpecification('7z')

    test_filter = file_entry_filters.SignaturesFileEntryFilter(
        specification_store, ['7z', 'bzip2'])

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
    test_filter_collection = file_entry_filters.FileEntryFilterCollection()

    self.assertEqual(len(test_filter_collection._filters), 0)

    file_entry_filter = file_entry_filters.NamesFileEntryFilter(['name'])
    test_filter_collection.AddFilter(file_entry_filter)
    self.assertEqual(len(test_filter_collection._filters), 1)

  def testHasFilters(self):
    """Tests the HasFilters function."""
    test_filter_collection = file_entry_filters.FileEntryFilterCollection()
    self.assertFalse(test_filter_collection.HasFilters())

    test_filter_collection = file_entry_filters.FileEntryFilterCollection()
    file_entry_filter = file_entry_filters.NamesFileEntryFilter(['name'])
    test_filter_collection.AddFilter(file_entry_filter)
    self.assertTrue(test_filter_collection.HasFilters())

  # TODO: add test for Matches.
  # TODO: add test for Print.


if __name__ == '__main__':
  unittest.main()
