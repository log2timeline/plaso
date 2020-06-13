#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This file contains a unit test for the timelib in Plaso."""

from __future__ import unicode_literals

import unittest

from plaso.lib import timelib

import pytz  # pylint: disable=wrong-import-order

from tests import test_lib as shared_test_lib


class TimeLibTest(shared_test_lib.BaseTestCase):
  """Tests for timestamp."""

  def testCopyToIsoFormat(self):
    """Test the CopyToIsoFormat function."""
    timezone = pytz.timezone('CET')

    timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-03-14 20:20:08.850041')
    date_time_string = timelib.Timestamp.CopyToIsoFormat(
        timestamp, timezone=timezone)
    self.assertEqual(date_time_string, '2013-03-14T21:20:08.850041+01:00')

  def testMonthDict(self):
    """Test the month dict, both inside and outside of scope."""
    self.assertEqual(timelib.MONTH_DICT['nov'], 11)
    self.assertEqual(timelib.MONTH_DICT['jan'], 1)
    self.assertEqual(timelib.MONTH_DICT['may'], 5)

    month = timelib.MONTH_DICT.get('doesnotexist')
    self.assertIsNone(month)

  def testLocaltimeToUTC(self):
    """Test the localtime to UTC conversion."""
    timezone = pytz.timezone('CET')

    local_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-01-01 01:00:00')
    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-01-01 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    local_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-07-01 02:00:00')
    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-07-01 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    # In the local timezone this is a non-existent timestamp.
    local_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-03-31 02:00:00')
    with self.assertRaises(pytz.NonExistentTimeError):
      timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone, is_dst=None)

    timestamp = timelib.Timestamp.LocaltimeToUTC(
        local_timestamp, timezone, is_dst=True)
    expected_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-03-31 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.LocaltimeToUTC(
        local_timestamp, timezone, is_dst=False)
    expected_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-03-31 01:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    # In the local timezone this is an ambiguous timestamp.
    local_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-10-27 02:30:00')

    with self.assertRaises(pytz.AmbiguousTimeError):
      timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone, is_dst=None)

    timestamp = timelib.Timestamp.LocaltimeToUTC(
        local_timestamp, timezone, is_dst=True)
    expected_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-10-27 00:30:00')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-10-27 01:30:00')
    self.assertEqual(timestamp, expected_timestamp)

    # Use the UTC timezone.
    self.assertEqual(
        timelib.Timestamp.LocaltimeToUTC(local_timestamp, pytz.UTC),
        local_timestamp)

    # Use a timezone in the Western Hemisphere.
    timezone = pytz.timezone('EST')

    local_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-01-01 00:00:00')
    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = shared_test_lib.CopyTimestampFromSring(
        '2013-01-01 05:00:00')
    self.assertEqual(timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
