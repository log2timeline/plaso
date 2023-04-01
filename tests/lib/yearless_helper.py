# -*- coding: utf-8 -*-
"""Tests for the year-less log format helper mix-in."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import yearless_helper
from plaso.parsers import mediator as parsers_mediator

from tests import test_lib as shared_test_lib


class YearLessLogFormatHelperTest(shared_test_lib.BaseTestCase):
  """Year-less log format definition helper mix-in tests."""

  # pylint: disable=protected-access

  def testGetYearsFromFileEntry(self):
    """Tests the _GetYearsFromFileEntry function."""
    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    test_helper = yearless_helper.YearLessLogFormatHelper()

    years = test_helper._GetYearsFromFileEntry(file_entry)
    self.assertEqual(years, set([2012]))

  def testGetMonthFromString(self):
    """Tests the _GetMonthFromString function."""
    test_helper = yearless_helper.YearLessLogFormatHelper()

    month = test_helper._GetMonthFromString('jan')
    self.assertEqual(month, 1)

    month = test_helper._GetMonthFromString('bogus')
    self.assertIsNone(month)

  def testGetRelativeYear(self):
    """Tests the _GetRelativeYear function."""
    test_helper = yearless_helper.YearLessLogFormatHelper()

    test_helper._SetMonthAndYear(11, 2022)

    relative_year = test_helper._GetRelativeYear()
    self.assertEqual(relative_year, 0)

  def testGetYear(self):
    """Tests the _GetYear function."""
    test_helper = yearless_helper.YearLessLogFormatHelper()

    test_helper._SetMonthAndYear(11, 2022)

    year = test_helper._GetYear()
    self.assertEqual(year, 2022)

  def testSetEstimatedYear(self):
    """Tests the _SetEstimatedYear function."""
    parser_mediator = parsers_mediator.ParserMediator()

    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    parser_mediator.SetFileEntry(file_entry)

    test_helper = yearless_helper.YearLessLogFormatHelper()

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 0)
    self.assertIsNone(test_helper._month)

    test_helper._SetEstimatedYear(parser_mediator)

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 2012)
    self.assertIsNone(test_helper._month)

    test_path = self._GetTestFilePath(['syslog.xz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    years = test_helper._GetYearsFromFileEntry(file_entry)

    compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
        compression_method=dfvfs_definitions.COMPRESSION_METHOD_XZ,
        parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        compressed_stream_path_spec)

    parser_mediator.SetFileEntry(file_entry)

    test_helper = yearless_helper.YearLessLogFormatHelper()

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 0)
    self.assertIsNone(test_helper._month)

    test_helper._SetEstimatedYear(parser_mediator)

    expected_year = min(years)

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, expected_year)
    self.assertIsNone(test_helper._month)

  def testSetMonthAndYear(self):
    """Tests the _SetMonthAndYear function."""
    test_helper = yearless_helper.YearLessLogFormatHelper()

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 0)
    self.assertIsNone(test_helper._month)

    test_helper._SetMonthAndYear(11, 2022)

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 2022)
    self.assertEqual(test_helper._month, 11)

  def testUpdateYear(self):
    """Tests the _UpdateYear function."""
    test_helper = yearless_helper.YearLessLogFormatHelper()

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 0)
    self.assertIsNone(test_helper._month)

    test_helper._UpdateYear(1)

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 0)
    self.assertEqual(test_helper._month, 1)

    test_helper._UpdateYear(5)

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 0)
    self.assertEqual(test_helper._month, 5)

    test_helper._UpdateYear(12)

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 0)
    self.assertEqual(test_helper._month, 12)

    test_helper._UpdateYear(1)

    self.assertEqual(test_helper._relative_year, 1)
    self.assertEqual(test_helper._year, 1)
    self.assertEqual(test_helper._month, 1)

    test_helper._UpdateYear(12)

    self.assertEqual(test_helper._relative_year, 0)
    self.assertEqual(test_helper._year, 0)
    self.assertEqual(test_helper._month, 12)

    test_helper._UpdateYear(5)

    self.assertEqual(test_helper._relative_year, 1)
    self.assertEqual(test_helper._year, 1)
    self.assertEqual(test_helper._month, 5)

    test_helper._UpdateYear(1)

    self.assertEqual(test_helper._relative_year, 2)
    self.assertEqual(test_helper._year, 2)
    self.assertEqual(test_helper._month, 1)

  def testGetYearLessLogHelper(self):
    """Tests the GetYearLessLogHelper function."""
    test_helper = yearless_helper.YearLessLogFormatHelper()

    year_less_log_helper = test_helper.GetYearLessLogHelper()
    self.assertIsNotNone(year_less_log_helper)


if __name__ == '__main__':
  unittest.main()
