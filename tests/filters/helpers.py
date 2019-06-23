#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter helper functions and classes."""

from __future__ import unicode_literals

import unittest

from plaso.filters import helpers

from tests import test_lib as shared_test_lib


class CopyValueToDateTimeTest(shared_test_lib.BaseTestCase):
  """Tests the CopyValueToDateTime helper function."""

  def testCopyValueToDateTime(self):
    """Tests the CopyValueToDateTime function."""
    date_time = helpers.CopyValueToDateTime('2009-07-13T23:29:02.849131')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    date_time = helpers.CopyValueToDateTime('2009-07-13')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247443200000000)

    date_time = helpers.CopyValueToDateTime('2009-07-13 23:29:02')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742000000)

    date_time = helpers.CopyValueToDateTime('2009-07-13 23:29:02.849131')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    date_time = helpers.CopyValueToDateTime('1247527742849131')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    date_time = helpers.CopyValueToDateTime(1247527742849131)
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    with self.assertRaises(ValueError):
      helpers.CopyValueToDateTime(None)


class GetUnicodeStringTest(shared_test_lib.BaseTestCase):
  """Tests the GetUnicodeString helper function."""

  def testGetUnicodeString(self):
    """Tests the GetUnicodeString function."""
    string = helpers.GetUnicodeString(['1', '2', '3'])
    self.assertEqual(string, '123')

    string = helpers.GetUnicodeString([1, 2, 3])
    self.assertEqual(string, '123')

    string = helpers.GetUnicodeString(123)
    self.assertEqual(string, '123')

    string = helpers.GetUnicodeString(b'123')
    self.assertEqual(string, '123')

    string = helpers.GetUnicodeString('123')
    self.assertEqual(string, '123')


class TimeRangeCacheTest(shared_test_lib.BaseTestCase):
  """Tests the TimeRangeCache helper."""

  # pylint: disable=protected-access

  def testGetTimeRange(self):
    """Tests the GetTimeRange function."""
    if hasattr(helpers.TimeRangeCache, '_lower'):
      del helpers.TimeRangeCache._lower
    if hasattr(helpers.TimeRangeCache, '_upper'):
      del helpers.TimeRangeCache._upper

    first, last = helpers.TimeRangeCache.GetTimeRange()
    self.assertEqual(first, helpers.TimeRangeCache._INT64_MIN)
    self.assertEqual(last, helpers.TimeRangeCache._INT64_MAX)

  def testSetLowerTimestamp(self):
    """Tests the SetLowerTimestamp function."""
    helpers.TimeRangeCache.SetLowerTimestamp(1247527742849131)

    first, last = helpers.TimeRangeCache.GetTimeRange()
    self.assertEqual(first, 1247527742849131)
    self.assertEqual(last, helpers.TimeRangeCache._INT64_MAX)

    del helpers.TimeRangeCache._lower

  def testSetUpperTimestamp(self):
    """Tests the SetUpperTimestamp function."""
    helpers.TimeRangeCache.SetUpperTimestamp(1247527742849131)

    first, last = helpers.TimeRangeCache.GetTimeRange()
    self.assertEqual(first, helpers.TimeRangeCache._INT64_MIN)
    self.assertEqual(last, 1247527742849131)

    del helpers.TimeRangeCache._upper


if __name__ == "__main__":
  unittest.main()
