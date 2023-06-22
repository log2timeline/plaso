# -*- coding: utf-8 -*-
"""Tests for the date-less log format helper mix-in."""

import datetime

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

  def test_GetDateFromFileEntry(self):
    """Tests the _GetDateFromFileEntry function."""
    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    test_helper = dateless_helper.DateLessLogFormatHelper()

    dates = test_helper._GetDatesFromFileEntry(file_entry)

    self.assertEqual(dates, {datetime.datetime(year=2012, month=7, day=28)})

  def test_GetDate(self):
    """Tests the _GetDate function."""
    test_helper = dateless_helper.DateLessLogFormatHelper()
    test_helper._SetDate(2013, 7, 22)

    date = test_helper._GetDate()

    self.assertEqual(date, datetime.datetime(year=2013, month=7, day=22))

    with self.assertRaises(ValueError):
      test_helper._SetDate(2013, 7, 32)

    with self.assertRaises(ValueError):
      test_helper._SetDate(2013, 13, 1)

  def test_SetDate(self):
    """Tests the _SetDate function."""
    test_helper = dateless_helper.DateLessLogFormatHelper()

    self.assertEqual(test_helper._date, None)

    test_helper._SetDate(2013, 7, 22)

    self.assertEqual(
        test_helper._date, datetime.datetime(year=2013, month=7, day=22))

  def test_SetEstimatedDate(self):
    """Tests the _SetEstimatedDate function."""
    parser_mediator = parsers_mediator.ParserMediator()

    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    parser_mediator.SetFileEntry(file_entry)

    test_helper = dateless_helper.DateLessLogFormatHelper()

    self.assertIsNone(test_helper._maximum_date)
    self.assertIsNone(test_helper._minimum_date)
    self.assertIsNone(test_helper._date)

    test_helper._SetEstimatedDate(parser_mediator)

    self.assertEqual(
        test_helper._maximum_date,
        datetime.datetime(year=2012, month=7, day=28))
    self.assertEqual(
        test_helper._minimum_date,
        datetime.datetime(year=2012, month=7, day=28))
    self.assertEqual(
        test_helper._date, datetime.datetime(year=2012, month=7, day=28))

  def test_GetDateLessLogHelper(self):
    """Tests the GetDateLessLogHelper function."""
    test_helper = dateless_helper.DateLessLogFormatHelper()

    date_less_log_helper = test_helper.GetDateLessLogHelper()
    self.assertIsNotNone(date_less_log_helper)


if __name__ == '__main__':
  unittest.main()
