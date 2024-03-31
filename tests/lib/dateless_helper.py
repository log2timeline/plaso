# -*- coding: utf-8 -*-
"""Tests for the date-less log format helper mix-in."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import dateless_helper
from plaso.parsers import mediator as parsers_mediator

from tests import test_lib as shared_test_lib


class DateLessLogFormatHelperTest(shared_test_lib.BaseTestCase):
  """Date-less log format definition helper mix-in tests."""

  # pylint: disable=protected-access

  def testGetDatesFromFileEntry(self):
    """Tests the _GetDatesFromFileEntry function."""
    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    test_helper = dateless_helper.DateLessLogFormatHelper()

    dates = test_helper._GetDatesFromFileEntry(file_entry)
    self.assertEqual(dates, set([tuple([2012, 7, 28])]))

  def testGetMonthFromString(self):
    """Tests the _GetMonthFromString function."""
    test_helper = dateless_helper.DateLessLogFormatHelper()

    month = test_helper._GetMonthFromString('jan')
    self.assertEqual(month, 1)

    month = test_helper._GetMonthFromString('bogus')
    self.assertIsNone(month)

  def testGetRelativeYear(self):
    """Tests the _GetRelativeYear function."""
    test_helper = dateless_helper.DateLessLogFormatHelper()

    test_helper._SetMonthAndYear(11, 2022)

    relative_year = test_helper._GetRelativeYear()
    self.assertEqual(relative_year, 0)

  def testGetYear(self):
    """Tests the _GetYear function."""
    test_helper = dateless_helper.DateLessLogFormatHelper()

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

    test_helper = dateless_helper.DateLessLogFormatHelper()

    self.assertEqual(test_helper._date, (0, 0, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

    test_helper._SetEstimatedYear(parser_mediator)

    self.assertEqual(test_helper._date, (2012, 0, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

    test_path = self._GetTestFilePath(['syslog.xz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    dates = test_helper._GetDatesFromFileEntry(file_entry)

    compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
        compression_method=dfvfs_definitions.COMPRESSION_METHOD_XZ,
        parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        compressed_stream_path_spec)

    parser_mediator.SetFileEntry(file_entry)

    test_helper = dateless_helper.DateLessLogFormatHelper()

    self.assertEqual(test_helper._date, (0, 0, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

    test_helper._SetEstimatedYear(parser_mediator)

    expected_date = min(dates)

    self.assertEqual(test_helper._date, (expected_date[0], 0, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

  def testSetMonthAndYear(self):
    """Tests the _SetMonthAndYear function."""
    test_helper = dateless_helper.DateLessLogFormatHelper()

    self.assertEqual(test_helper._date, (0, 0, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

    test_helper._SetMonthAndYear(11, 2022)

    self.assertEqual(test_helper._date, (2022, 11, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

  def testUpdateYear(self):
    """Tests the _UpdateYear function."""
    test_helper = dateless_helper.DateLessLogFormatHelper()

    self.assertEqual(test_helper._date, (0, 0, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

    test_helper._UpdateYear(1)

    self.assertEqual(test_helper._date, (0, 1, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

    test_helper._UpdateYear(5)

    self.assertEqual(test_helper._date, (0, 5, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

    test_helper._UpdateYear(12)

    self.assertEqual(test_helper._date, (0, 12, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

    test_helper._UpdateYear(1)

    self.assertEqual(test_helper._date, (1, 1, 0))
    self.assertEqual(test_helper._relative_date, (1, 0, 0))

    test_helper._UpdateYear(12)

    self.assertEqual(test_helper._date, (0, 12, 0))
    self.assertEqual(test_helper._relative_date, (0, 0, 0))

    test_helper._UpdateYear(5)

    self.assertEqual(test_helper._date, (1, 5, 0))
    self.assertEqual(test_helper._relative_date, (1, 0, 0))

    test_helper._UpdateYear(1)

    self.assertEqual(test_helper._date, (2, 1, 0))
    self.assertEqual(test_helper._relative_date, (2, 0, 0))

  def testGetDateLessLogHelper(self):
    """Tests the GetDateLessLogHelper function."""
    test_helper = dateless_helper.DateLessLogFormatHelper()

    date_less_log_helper = test_helper.GetDateLessLogHelper()
    self.assertIsNotNone(date_less_log_helper)


if __name__ == '__main__':
  unittest.main()
