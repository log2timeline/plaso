#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains a unit test for the timelib in Plaso."""

import datetime
import unittest
import uuid

from plaso.lib import errors
from plaso.lib import timelib

import pytz


class TimeLibTest(unittest.TestCase):
  """Tests for timestamp."""

  def testCopyFromString(self):
    """Tests the CopyFromString function."""
    timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27')
    expected_timestamp = 1340755200000000
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(None)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-6-27')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-00-27')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-13-27')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-01-00')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-01-32')

    timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
    expected_timestamp = 1340821021000000
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:1')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27T18:17:01')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 24:17:01')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:60:01')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:60')

    timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01.123')
    expected_timestamp = 1340821021123000
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01.')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01.12')

    timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01.123456')
    expected_timestamp = 1340821021123456
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01.1234')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01.1234567')

    timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01+00:00')
    expected_timestamp = 1340821021000000
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01+01:00')
    expected_timestamp = 1340817421000000
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01-07:00')
    expected_timestamp = 1340846221000000
    self.assertEqual(timestamp, expected_timestamp)

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01+1')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01+01')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01+01:0')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01+00:00:0')

    with self.assertRaises(ValueError):
      _ = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01Z')

  def testCocoaTime(self):
    """Tests the Cocoa timestamp conversion."""
    timestamp = timelib.Timestamp.FromCocoaTime(395011845)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-08 21:30:45')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromCocoaTime(395353142)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-12 20:19:02')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromCocoaTime(394993669)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-08 16:27:49')
    self.assertEqual(timestamp, expected_timestamp)

  def testHFSTimes(self):
    """Tests the HFS timestamp conversion."""
    timestamp = timelib.Timestamp.FromHfsTime(
        3458215528, timezone=pytz.timezone(u'EST5EDT'), is_dst=True)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 15:25:28-04:00')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromHfsPlusTime(3458215528)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 15:25:28')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromHfsPlusTime(3413373928)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-02-29 15:25:28')
    self.assertEqual(timestamp, expected_timestamp)

  def testTimestampIsLeapYear(self):
    """Tests the is leap year check."""
    self.assertEqual(timelib.Timestamp.IsLeapYear(2012), True)
    self.assertEqual(timelib.Timestamp.IsLeapYear(2013), False)
    self.assertEqual(timelib.Timestamp.IsLeapYear(2000), True)
    self.assertEqual(timelib.Timestamp.IsLeapYear(1900), False)

  def testTimestampDaysInMonth(self):
    """Tests the days in month function."""
    self.assertEqual(timelib.Timestamp.DaysInMonth(0, 2013), 31)
    self.assertEqual(timelib.Timestamp.DaysInMonth(1, 2013), 28)
    self.assertEqual(timelib.Timestamp.DaysInMonth(1, 2012), 29)
    self.assertEqual(timelib.Timestamp.DaysInMonth(2, 2013), 31)
    self.assertEqual(timelib.Timestamp.DaysInMonth(3, 2013), 30)
    self.assertEqual(timelib.Timestamp.DaysInMonth(4, 2013), 31)
    self.assertEqual(timelib.Timestamp.DaysInMonth(5, 2013), 30)
    self.assertEqual(timelib.Timestamp.DaysInMonth(6, 2013), 31)
    self.assertEqual(timelib.Timestamp.DaysInMonth(7, 2013), 31)
    self.assertEqual(timelib.Timestamp.DaysInMonth(8, 2013), 30)
    self.assertEqual(timelib.Timestamp.DaysInMonth(9, 2013), 31)
    self.assertEqual(timelib.Timestamp.DaysInMonth(10, 2013), 30)
    self.assertEqual(timelib.Timestamp.DaysInMonth(11, 2013), 31)

    with self.assertRaises(ValueError):
      timelib.Timestamp.DaysInMonth(-1, 2013)

    with self.assertRaises(ValueError):
      timelib.Timestamp.DaysInMonth(12, 2013)

  def testTimestampDaysInYear(self):
    """Test the days in year function."""
    self.assertEqual(timelib.Timestamp.DaysInYear(2013), 365)
    self.assertEqual(timelib.Timestamp.DaysInYear(2012), 366)

  def testTimestampDayOfYear(self):
    """Test the day of year function."""
    self.assertEqual(timelib.Timestamp.DayOfYear(0, 0, 2013), 0)
    self.assertEqual(timelib.Timestamp.DayOfYear(0, 2, 2013), 31 + 28)
    self.assertEqual(timelib.Timestamp.DayOfYear(0, 2, 2012), 31 + 29)

    expected_day_of_year = 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30
    self.assertEqual(
        timelib.Timestamp.DayOfYear(0, 11, 2013), expected_day_of_year)

  def testTimestampFromDelphiTime(self):
    """Test the Delphi date time conversion."""
    timestamp = timelib.Timestamp.FromDelphiTime(41443.8263953)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-06-18 19:50:00')
    self.assertEqual(timestamp, expected_timestamp)

  def testTimestampFromFatDateTime(self):
    """Test the FAT date time conversion."""
    timestamp = timelib.Timestamp.FromFatDateTime(0xa8d03d0c)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-08-12 21:06:32')
    self.assertEqual(timestamp, expected_timestamp)

    # Invalid number of seconds.
    fat_date_time = (0xa8d03d0c & ~(0x1f << 16)) | ((30 & 0x1f) << 16)
    self.assertEqual(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid number of minutes.
    fat_date_time = (0xa8d03d0c & ~(0x3f << 21)) | ((60 & 0x3f) << 21)
    self.assertEqual(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid number of hours.
    fat_date_time = (0xa8d03d0c & ~(0x1f << 27)) | ((24 & 0x1f) << 27)
    self.assertEqual(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid day of month.
    fat_date_time = (0xa8d03d0c & ~0x1f) | (32 & 0x1f)
    self.assertEqual(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid month.
    fat_date_time = (0xa8d03d0c & ~(0x0f << 5)) | ((13 & 0x0f) << 5)
    self.assertEqual(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

  def testTimestampFromFiletime(self):
    """Test the FILETIME conversion."""
    timestamp = timelib.Timestamp.FromFiletime(0x01cb3a623d0a17ce)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-08-12 21:06:31.546875')
    self.assertEqual(timestamp, expected_timestamp)

    filetime = 86400 * 10000000
    timestamp = timelib.Timestamp.FromFiletime(filetime)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'1601-01-02 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    # FILETIME that exceeds lower bound.
    filetime = -1
    self.assertEqual(timelib.Timestamp.FromFiletime(filetime), 0)

  def testTimestampFromPosixTime(self):
    """Test the POSIX time conversion."""
    timestamp = timelib.Timestamp.FromPosixTime(1281647191)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-08-12 21:06:31')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromPosixTime(-122557518)
    expected_timestamp = timelib.Timestamp.FromTimeString(
        u'1966-02-12 1966 12:14:42 UTC')
    self.assertEqual(timestamp, expected_timestamp)

    # POSIX time that exceeds upper bound.
    self.assertEqual(timelib.Timestamp.FromPosixTime(9223372036855), 0)

    # POSIX time that exceeds lower bound.
    self.assertEqual(timelib.Timestamp.FromPosixTime(-9223372036855), 0)

  def testTimestampFromUUIDTime(self):
    """Test the UUID time conversion."""
    uuid_object = uuid.UUID(u'00911b54-9ef4-11e1-be53-525400123456')

    timestamp = timelib.Timestamp.FromUUIDTime(uuid_object.time)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-16 01:11:01.654408')
    self.assertEqual(timestamp, expected_timestamp)

    uuid_time = 86400 * 10000000
    timestamp = timelib.Timestamp.FromUUIDTime(uuid_time)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'1582-10-16 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    # UUID time that exceeds lower bound.
    uuid_time = -1
    self.assertEqual(timelib.Timestamp.FromUUIDTime(uuid_time), 0)

  def testTimestampFromWebKitTime(self):
    """Test the WebKit time conversion."""
    timestamp = timelib.Timestamp.FromWebKitTime(0x2dec3d061a9bfb)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-08-12 21:06:31.546875')
    self.assertEqual(timestamp, expected_timestamp)

    webkit_time = 86400 * 1000000
    timestamp = timelib.Timestamp.FromWebKitTime(webkit_time)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'1601-01-02 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    # WebKit time that exceeds lower bound.
    webkit_time = -((1 << 63L) - 1)
    self.assertEqual(timelib.Timestamp.FromWebKitTime(webkit_time), 0)

  def testMonthDict(self):
    """Test the month dict, both inside and outside of scope."""
    self.assertEqual(timelib.MONTH_DICT[u'nov'], 11)
    self.assertEqual(timelib.MONTH_DICT[u'jan'], 1)
    self.assertEqual(timelib.MONTH_DICT[u'may'], 5)

    month = timelib.MONTH_DICT.get(u'doesnotexist')
    self.assertEqual(month, None)

  def testLocaltimeToUTC(self):
    """Test the localtime to UTC conversion."""
    timezone = pytz.timezone(u'CET')

    local_timestamp = timelib.Timestamp.CopyFromString(u'2013-01-01 01:00:00')
    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-01-01 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    local_timestamp = timelib.Timestamp.CopyFromString(u'2013-07-01 02:00:00')
    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-01 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    # In the local timezone this is a non-existent timestamp.
    local_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-03-31 02:00:00')
    with self.assertRaises(pytz.NonExistentTimeError):
      timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone, is_dst=None)

    timestamp = timelib.Timestamp.LocaltimeToUTC(
        local_timestamp, timezone, is_dst=True)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-03-31 00:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.LocaltimeToUTC(
        local_timestamp, timezone, is_dst=False)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-03-31 01:00:00')
    self.assertEqual(timestamp, expected_timestamp)

    # In the local timezone this is an ambiguous timestamp.
    local_timestamp = timelib.Timestamp.CopyFromString(u'2013-10-27 02:30:00')

    with self.assertRaises(pytz.AmbiguousTimeError):
      timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone, is_dst=None)

    timestamp = timelib.Timestamp.LocaltimeToUTC(
        local_timestamp, timezone, is_dst=True)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-27 00:30:00')
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-27 01:30:00')
    self.assertEqual(timestamp, expected_timestamp)

    # Use the UTC timezone.
    self.assertEqual(
        timelib.Timestamp.LocaltimeToUTC(local_timestamp, pytz.UTC),
        local_timestamp)

    # Use a timezone in the Western Hemisphere.
    timezone = pytz.timezone(u'EST')

    local_timestamp = timelib.Timestamp.CopyFromString(u'2013-01-01 00:00:00')
    timestamp = timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-01-01 05:00:00')
    self.assertEqual(timestamp, expected_timestamp)

  def testCopyToDatetime(self):
    """Test the copy to datetime object."""
    timezone = pytz.timezone(u'CET')

    timestamp = timelib.Timestamp.CopyFromString(u'2013-03-14 20:20:08.850041')
    datetime_object = timelib.Timestamp.CopyToDatetime(timestamp, timezone)
    expected_datetime_object = datetime.datetime(
        2013, 3, 14, 21, 20, 8, 850041, tzinfo=timezone)
    self.assertEqual(datetime_object, expected_datetime_object)

  def testCopyToPosix(self):
    """Test converting microseconds to seconds."""
    timestamp = timelib.Timestamp.CopyFromString(u'2013-10-01 12:00:00')
    expected_posixtime, _ = divmod(timestamp, 1000000)
    posixtime = timelib.Timestamp.CopyToPosix(timestamp)
    self.assertEqual(posixtime, expected_posixtime)

  def testTimestampFromTimeString(self):
    """The the FromTimeString function."""
    # Test daylight savings.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-01 12:00:00')

    # Check certain variance of this timestamp.
    timestamp = timelib.Timestamp.FromTimeString(
        u'2013-10-01 14:00:00', timezone=pytz.timezone(u'Europe/Rome'))
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        u'2013-10-01 12:00:00', timezone=pytz.timezone(u'UTC'))
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        u'2013-10-01 05:00:00', timezone=pytz.timezone(u'PST8PDT'))
    self.assertEqual(timestamp, expected_timestamp)

    # Now to test outside of the daylight savings.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-02-01 12:00:00')

    timestamp = timelib.Timestamp.FromTimeString(
        u'2014-02-01 13:00:00', timezone=pytz.timezone(u'Europe/Rome'))
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        u'2014-02-01 12:00:00', timezone=pytz.timezone(u'UTC'))
    self.assertEqual(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        u'2014-02-01 04:00:00', timezone=pytz.timezone(u'PST8PDT'))
    self.assertEqual(timestamp, expected_timestamp)

    # Define two timestamps, one being GMT and the other UTC.
    time_string_utc = u'Wed 05 May 2010 03:52:31 UTC'
    time_string_gmt = u'Wed 05 May 2010 03:52:31 GMT'

    timestamp_utc = timelib.Timestamp.FromTimeString(time_string_utc)
    timestamp_gmt = timelib.Timestamp.FromTimeString(time_string_gmt)

    # Test if these two are different, and if so, then we'll try again
    # using the 'gmt_is_utc' flag, which then should result to the same
    # results.
    if timestamp_utc != timestamp_gmt:
      self.assertEqual(timestamp_utc, timelib.Timestamp.FromTimeString(
          time_string_gmt, gmt_as_timezone=False))

    timestamp = timelib.Timestamp.FromTimeString(
        u'12-15-1984 05:13:00', timezone=pytz.timezone(u'EST5EDT'))
    self.assertEqual(timestamp, 471953580000000)

    # Swap day and month.
    timestamp = timelib.Timestamp.FromTimeString(
        u'12-10-1984 05:13:00', timezone=pytz.timezone(u'EST5EDT'),
        dayfirst=True)
    self.assertEqual(timestamp, 466420380000000)

    timestamp = timelib.Timestamp.FromTimeString(u'12-15-1984 10:13:00Z')
    self.assertEqual(timestamp, 471953580000000)

    # Setting the timezone for string that already contains a timezone
    # indicator should not affect the conversion.
    timestamp = timelib.Timestamp.FromTimeString(
        u'12-15-1984 10:13:00Z', timezone=pytz.timezone(u'EST5EDT'))
    self.assertEqual(timestamp, 471953580000000)

    timestamp = timelib.Timestamp.FromTimeString(u'15/12/1984 10:13:00Z')
    self.assertEqual(timestamp, 471953580000000)

    timestamp = timelib.Timestamp.FromTimeString(u'15-12-84 10:13:00Z')
    self.assertEqual(timestamp, 471953580000000)

    timestamp = timelib.Timestamp.FromTimeString(
        u'15-12-84 10:13:00-04', timezone=pytz.timezone(u'EST5EDT'))
    self.assertEqual(timestamp, 471967980000000)

    with self.assertRaises(errors.TimestampError):
      timestamp = timelib.Timestamp.FromTimeString(
          u'thisisnotadatetime', timezone=pytz.timezone(u'EST5EDT'))

    timestamp = timelib.Timestamp.FromTimeString(
        u'12-15-1984 04:13:00', timezone=pytz.timezone(u'America/Chicago'))
    self.assertEqual(timestamp, 471953580000000)

    timestamp = timelib.Timestamp.FromTimeString(
        u'07-14-1984 23:13:00', timezone=pytz.timezone(u'America/Chicago'))
    self.assertEqual(timestamp, 458712780000000)

    timestamp = timelib.Timestamp.FromTimeString(
        u'12-15-1984 05:13:00', timezone=pytz.timezone(u'US/Pacific'))
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

  def testTimestampFromTimeParts(self):
    """Test the FromTimeParts function."""
    timestamp = timelib.Timestamp.FromTimeParts(
        2013, 6, 25, 22, 19, 46, 0, timezone=pytz.timezone(u'PST8PDT'))
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-06-25 22:19:46-07:00')
    self.assertEqual(timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-06-26 05:19:46')
    timestamp = timelib.Timestamp.FromTimeParts(2013, 6, 26, 5, 19, 46)
    self.assertEqual(timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-06-26 05:19:46.000542')
    timestamp = timelib.Timestamp.FromTimeParts(2013, 6, 26, 5, 19, 46, 542)
    self.assertEqual(timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
