#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This file contains a unit test for the timelib in Plaso."""

from __future__ import unicode_literals

import unittest

from plaso.lib import errors
from plaso.lib import timelib

import pytz  # pylint: disable=wrong-import-order


class TimeLibTest(unittest.TestCase):
  """Tests for timestamp."""

  def testCopyFromString(self):
    """Tests the CopyFromString function."""
    timestamp = timelib.Timestamp.CopyFromString('2012-06-27')
    expected_timestamp = 1340755200000000
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(None)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-6-27')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-00-27')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-13-27')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-01-00')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-01-32')

    timestamp = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01')
    expected_timestamp = 1340821021000000
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:1')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27T18:17:01')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 24:17:01')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:60:01')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:60')

    timestamp = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01.123')
    expected_timestamp = 1340821021123000
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01.')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01.12')

    timestamp = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01.123456')
    expected_timestamp = 1340821021123456
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01.1234')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01.1234567')

    timestamp = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01+00:00')
    expected_timestamp = 1340821021000000
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01+01:00')
    expected_timestamp = 1340817421000000
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01-07:00')
    expected_timestamp = 1340846221000000
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01+1')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01+01')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01+01:0')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01+00:00:0')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString('2012-06-27 18:17:01Z')

  def testCopyToIsoFormat(self):
    """Test the CopyToIsoFormat function."""
    timezone = pytz.timezone('CET')

    timestamp = timelib.Timestamp.CopyFromString('2013-03-14 20:20:08.850041')
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

    local_timestamp = timelib.Timestamp.CopyFromString('2013-01-01 01:00:00')
    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-01-01 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    local_timestamp = timelib.Timestamp.CopyFromString('2013-07-01 02:00:00')
    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-07-01 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    # In the local timezone this is a non-existent timestamp.
    local_timestamp = timelib.Timestamp.CopyFromString(
        '2013-03-31 02:00:00')
    with self.assertRaises(pytz.NonExistentTimeError):
      timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone, is_dst=None)

    timestamp = timelib.Timestamp.LocaltimeToUTC(
        local_timestamp, timezone, is_dst=True)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-03-31 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.LocaltimeToUTC(
        local_timestamp, timezone, is_dst=False)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-03-31 01:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    # In the local timezone this is an ambiguous timestamp.
    local_timestamp = timelib.Timestamp.CopyFromString('2013-10-27 02:30:00')

    with self.assertRaises(pytz.AmbiguousTimeError):
      timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone, is_dst=None)

    timestamp = timelib.Timestamp.LocaltimeToUTC(
        local_timestamp, timezone, is_dst=True)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-10-27 00:30:00')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-10-27 01:30:00')
    self.assertEqual(timestamp, expected_timestamp)

    # Use the UTC timezone.
    self.assertEqual(
        timelib.Timestamp.LocaltimeToUTC(local_timestamp, pytz.UTC),
        local_timestamp)

    # Use a timezone in the Western Hemisphere.
    timezone = pytz.timezone('EST')

    local_timestamp = timelib.Timestamp.CopyFromString('2013-01-01 00:00:00')
    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-01-01 05:00:00')
    self.assertEqual(timestamp, expected_timestamp)

  def testTimestampFromTimeString(self):
    """The the FromTimeString function."""
    # Test daylight savings.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-10-01 12:00:00')

    # Check certain variance of this timestamp.
    timestamp = timelib.Timestamp.FromTimeString(
        '2013-10-01 14:00:00', timezone=pytz.timezone('Europe/Rome'))
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        '2013-10-01 12:00:00', timezone=pytz.timezone('UTC'))
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        '2013-10-01 05:00:00', timezone=pytz.timezone('PST8PDT'))
    self.assertEqual(timestamp, expected_timestamp)

    # Now to test outside of the daylight savings.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2014-02-01 12:00:00')

    timestamp = timelib.Timestamp.FromTimeString(
        '2014-02-01 13:00:00', timezone=pytz.timezone('Europe/Rome'))
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        '2014-02-01 12:00:00', timezone=pytz.timezone('UTC'))
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        '2014-02-01 04:00:00', timezone=pytz.timezone('PST8PDT'))
    self.assertEqual(timestamp, expected_timestamp)

    # Define two timestamps, one being GMT and the other UTC.
    time_string_utc = 'Wed 05 May 2010 03:52:31 UTC'
    time_string_gmt = 'Wed 05 May 2010 03:52:31 GMT'

    timestamp_utc = timelib.Timestamp.FromTimeString(time_string_utc)
    timestamp_gmt = timelib.Timestamp.FromTimeString(time_string_gmt)

    # Test if these two are different, and if so, then we'll try again
    # using the 'gmt_is_utc' flag, which then should result to the same
    # results.
    if timestamp_utc != timestamp_gmt:
      self.assertEqual(timestamp_utc, timelib.Timestamp.FromTimeString(
          time_string_gmt, gmt_as_timezone=False))

    timestamp = timelib.Timestamp.FromTimeString(
        '12-15-1984 05:13:00', timezone=pytz.timezone('EST5EDT'))
    self.assertEqual(timestamp, 471953580000000)

    # Swap day and month.
    timestamp = timelib.Timestamp.FromTimeString(
        '12-10-1984 05:13:00', timezone=pytz.timezone('EST5EDT'),
        dayfirst=True)
    self.assertEqual(timestamp, 466420380000000)

    timestamp = timelib.Timestamp.FromTimeString('12-15-1984 10:13:00Z')
    self.assertEqual(timestamp, 471953580000000)

    # Setting the timezone for string that already contains a timezone
    # indicator should not affect the conversion.
    timestamp = timelib.Timestamp.FromTimeString(
        '12-15-1984 10:13:00Z', timezone=pytz.timezone('EST5EDT'))
    self.assertEqual(timestamp, 471953580000000)

    timestamp = timelib.Timestamp.FromTimeString('15/12/1984 10:13:00Z')
    self.assertEqual(timestamp, 471953580000000)

    timestamp = timelib.Timestamp.FromTimeString('15-12-84 10:13:00Z')
    self.assertEqual(timestamp, 471953580000000)

    timestamp = timelib.Timestamp.FromTimeString(
        '15-12-84 10:13:00-04', timezone=pytz.timezone('EST5EDT'))
    self.assertEqual(timestamp, 471967980000000)

    with self.assertRaises(errors.TimestampError):
      timestamp = timelib.Timestamp.FromTimeString(
          'thisisnotadatetime', timezone=pytz.timezone('EST5EDT'))

    timestamp = timelib.Timestamp.FromTimeString(
        '12-15-1984 04:13:00', timezone=pytz.timezone('America/Chicago'))
    self.assertEqual(timestamp, 471953580000000)

    timestamp = timelib.Timestamp.FromTimeString(
        '07-14-1984 23:13:00', timezone=pytz.timezone('America/Chicago'))
    self.assertEqual(timestamp, 458712780000000)

    timestamp = timelib.Timestamp.FromTimeString(
        '12-15-1984 05:13:00', timezone=pytz.timezone('US/Pacific'))
    self.assertEqual(timestamp, 471964380000000)

  def testRoundTimestamp(self):
    """Test the RoundToSeconds function."""
    # Should be rounded up.
    test_one = 442813351785412
    # Should be rounded down.
    test_two = 1384381247271976

    self.assertEqual(
        timelib.Timestamp.RoundToSeconds(test_one), 442813352000000)
    self.assertEqual(
        timelib.Timestamp.RoundToSeconds(test_two), 1384381247000000)


if __name__ == '__main__':
  unittest.main()
