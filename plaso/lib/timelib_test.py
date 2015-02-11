#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains a unit test for the timelib in Plaso."""

import calendar
import datetime
import unittest

from plaso.lib import timelib

import pytz


def CopyStringToTimestamp(time_string):
  """Copies a string containing a date and time value to a timestamp.

  Test function that does not rely on dateutil parser.

  Args:
    time_string: A string containing a date and time value formatted as:
                 YYYY-MM-DD hh:mm:ss.######[+-]##:##
                 Where # are numeric digits ranging from 0 to 9 and the seconds
                 fraction can be either 3 or 6 digits. Both the seconds fraction
                 and timezone offset are optional. The default timezone is UTC.

  Returns:
    An integer containing the timestamp.

  Raises:
    ValueError: if the time string is invalid or not supported.
  """
  time_string_length = len(time_string)

  # The time string should at least contain 'YYYY-MM-DD hh:mm:ss'.
  if (time_string_length < 19 or time_string[4] != '-' or
      time_string[7] != '-' or time_string[10] != ' ' or
      time_string[13] != ':' or time_string[16] != ':'):
    raise ValueError(u'Invalid time string.')

  try:
    year = int(time_string[0:4], 10)
  except ValueError:
    raise ValueError(u'Unable to parse year.')

  try:
    month = int(time_string[5:7], 10)
  except ValueError:
    raise ValueError(u'Unable to parse month.')

  if month not in range(1, 13):
    raise ValueError(u'Month value out of bounds.')

  try:
    day_of_month = int(time_string[8:10], 10)
  except ValueError:
    raise ValueError(u'Unable to parse day of month.')

  if day_of_month not in range(1, 32):
    raise ValueError(u'Day of month value out of bounds.')

  try:
    hours = int(time_string[11:13], 10)
  except ValueError:
    raise ValueError(u'Unable to parse hours.')

  if hours not in range(0, 24):
    raise ValueError(u'Hours value out of bounds.')

  try:
    minutes = int(time_string[14:16], 10)
  except ValueError:
    raise ValueError(u'Unable to parse minutes.')

  if minutes not in range(0, 60):
    raise ValueError(u'Minutes value out of bounds.')

  try:
    seconds = int(time_string[17:19], 10)
  except ValueError:
    raise ValueError(u'Unable to parse day of seconds.')

  if seconds not in range(0, 60):
    raise ValueError(u'Seconds value out of bounds.')

  micro_seconds = 0
  timezone_offset = 0

  if time_string_length > 19:
    if time_string[19] != '.':
      timezone_index = 19
    else:
      for timezone_index in range(19, time_string_length):
        if time_string[timezone_index] in ['+', '-']:
          break

        # The calculation that follow rely on the timezone index to point
        # beyond the string in case no timezone offset was defined.
        if timezone_index == time_string_length - 1:
          timezone_index += 1

    if timezone_index > 19:
      fraction_of_seconds_length = timezone_index - 20
      if fraction_of_seconds_length not in [3, 6]:
        raise ValueError(u'Invalid time string.')

      try:
        micro_seconds = int(time_string[20:timezone_index], 10)
      except ValueError:
        raise ValueError(u'Unable to parse fraction of seconds.')

      if fraction_of_seconds_length == 3:
        micro_seconds *= 1000

    if timezone_index < time_string_length:
      if (time_string_length - timezone_index != 6 or
          time_string[timezone_index + 3] != ':'):
        raise ValueError(u'Invalid time string.')

      try:
        timezone_offset = int(time_string[
            timezone_index + 1:timezone_index + 3])
      except ValueError:
        raise ValueError(u'Unable to parse timezone hours offset.')

      if timezone_offset not in range(0, 24):
        raise ValueError(u'Timezone hours offset value out of bounds.')

      # Note that when the sign of the timezone offset is negative
      # the difference needs to be added. We do so by flipping the sign.
      if time_string[timezone_index] == '-':
        timezone_offset *= 60
      else:
        timezone_offset *= -60

      try:
        timezone_offset += int(time_string[
            timezone_index + 4:timezone_index + 6])
      except ValueError:
        raise ValueError(u'Unable to parse timezone minutes offset.')

      timezone_offset *= 60

  timestamp = int(calendar.timegm((
      year, month, day_of_month, hours, minutes, seconds)))

  return ((timestamp + timezone_offset) * 1000000) + micro_seconds


class TimeLibUnitTest(unittest.TestCase):
  """A unit test for the timelib."""

  def testCocoaTime(self):
    """Tests the Cocoa timestamp conversion."""
    self.assertEquals(
        timelib.Timestamp.FromCocoaTime(395011845),
        CopyStringToTimestamp('2013-07-08 21:30:45'))

    self.assertEquals(
        timelib.Timestamp.FromCocoaTime(395353142),
        CopyStringToTimestamp('2013-07-12 20:19:02'))

    self.assertEquals(
        timelib.Timestamp.FromCocoaTime(394993669),
        CopyStringToTimestamp('2013-07-08 16:27:49'))

  def testHFSTimes(self):
    """Tests the HFS timestamp conversion."""
    self.assertEquals(
        timelib.Timestamp.FromHfsTime(
            3458215528, timezone=pytz.timezone('EST5EDT'), is_dst=True),
        CopyStringToTimestamp('2013-08-01 15:25:28-04:00'))

    self.assertEquals(
        timelib.Timestamp.FromHfsPlusTime(3458215528),
        CopyStringToTimestamp('2013-08-01 15:25:28'))

    self.assertEquals(
        timelib.Timestamp.FromHfsPlusTime(3413373928),
        CopyStringToTimestamp('2012-02-29 15:25:28'))

  def testTimestampIsLeapYear(self):
    """Tests the is leap year check."""
    self.assertEquals(timelib.Timestamp.IsLeapYear(2012), True)
    self.assertEquals(timelib.Timestamp.IsLeapYear(2013), False)
    self.assertEquals(timelib.Timestamp.IsLeapYear(2000), True)
    self.assertEquals(timelib.Timestamp.IsLeapYear(1900), False)

  def testTimestampDaysInMonth(self):
    """Tests the days in month function."""
    self.assertEquals(timelib.Timestamp.DaysInMonth(0, 2013), 31)
    self.assertEquals(timelib.Timestamp.DaysInMonth(1, 2013), 28)
    self.assertEquals(timelib.Timestamp.DaysInMonth(1, 2012), 29)
    self.assertEquals(timelib.Timestamp.DaysInMonth(2, 2013), 31)
    self.assertEquals(timelib.Timestamp.DaysInMonth(3, 2013), 30)
    self.assertEquals(timelib.Timestamp.DaysInMonth(4, 2013), 31)
    self.assertEquals(timelib.Timestamp.DaysInMonth(5, 2013), 30)
    self.assertEquals(timelib.Timestamp.DaysInMonth(6, 2013), 31)
    self.assertEquals(timelib.Timestamp.DaysInMonth(7, 2013), 31)
    self.assertEquals(timelib.Timestamp.DaysInMonth(8, 2013), 30)
    self.assertEquals(timelib.Timestamp.DaysInMonth(9, 2013), 31)
    self.assertEquals(timelib.Timestamp.DaysInMonth(10, 2013), 30)
    self.assertEquals(timelib.Timestamp.DaysInMonth(11, 2013), 31)

    with self.assertRaises(ValueError):
      timelib.Timestamp.DaysInMonth(-1, 2013)

    with self.assertRaises(ValueError):
      timelib.Timestamp.DaysInMonth(12, 2013)

  def testTimestampDaysInYear(self):
    """Test the days in year function."""
    self.assertEquals(timelib.Timestamp.DaysInYear(2013), 365)
    self.assertEquals(timelib.Timestamp.DaysInYear(2012), 366)

  def testTimestampDayOfYear(self):
    """Test the day of year function."""
    self.assertEquals(timelib.Timestamp.DayOfYear(0, 0, 2013), 0)
    self.assertEquals(timelib.Timestamp.DayOfYear(0, 2, 2013), 31 + 28)
    self.assertEquals(timelib.Timestamp.DayOfYear(0, 2, 2012), 31 + 29)
    self.assertEquals(timelib.Timestamp.DayOfYear(0, 11, 2013),
                      31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30)

  def testTimestampFromDelphiTime(self):
    """Test the Delphi date time conversion."""
    self.assertEquals(
        timelib.Timestamp.FromDelphiTime(41443.8263953),
        CopyStringToTimestamp('2013-06-18 19:50:00'))

  def testTimestampFromFatDateTime(self):
    """Test the FAT date time conversion."""
    self.assertEquals(
        timelib.Timestamp.FromFatDateTime(0xa8d03d0c),
        CopyStringToTimestamp('2010-08-12 21:06:32'))

    # Invalid number of seconds.
    fat_date_time = (0xa8d03d0c & ~(0x1f << 16)) | ((30 & 0x1f) << 16)
    self.assertEquals(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid number of minutes.
    fat_date_time = (0xa8d03d0c & ~(0x3f << 21)) | ((60 & 0x3f) << 21)
    self.assertEquals(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid number of hours.
    fat_date_time = (0xa8d03d0c & ~(0x1f << 27)) | ((24 & 0x1f) << 27)
    self.assertEquals(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid day of month.
    fat_date_time = (0xa8d03d0c & ~0x1f) | (32 & 0x1f)
    self.assertEquals(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid month.
    fat_date_time = (0xa8d03d0c & ~(0x0f << 5)) | ((13 & 0x0f) << 5)
    self.assertEquals(timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

  def testTimestampFromWebKitTime(self):
    """Test the WebKit time conversion."""
    self.assertEquals(
        timelib.Timestamp.FromWebKitTime(0x2dec3d061a9bfb),
        CopyStringToTimestamp('2010-08-12 21:06:31.546875'))

    webkit_time = 86400 * 1000000
    self.assertEquals(
        timelib.Timestamp.FromWebKitTime(webkit_time),
        CopyStringToTimestamp('1601-01-02 00:00:00'))

    # WebKit time that exceeds lower bound.
    webkit_time = -((1 << 63L) - 1)
    self.assertEquals(timelib.Timestamp.FromWebKitTime(webkit_time), 0)

  def testTimestampFromFiletime(self):
    """Test the FILETIME conversion."""
    self.assertEquals(
        timelib.Timestamp.FromFiletime(0x01cb3a623d0a17ce),
        CopyStringToTimestamp('2010-08-12 21:06:31.546875'))

    filetime = 86400 * 10000000
    self.assertEquals(
        timelib.Timestamp.FromFiletime(filetime),
        CopyStringToTimestamp('1601-01-02 00:00:00'))

    # FILETIME that exceeds lower bound.
    filetime = -1
    self.assertEquals(timelib.Timestamp.FromFiletime(filetime), 0)

  def testTimestampFromPosixTime(self):
    """Test the POSIX time conversion."""
    self.assertEquals(
        timelib.Timestamp.FromPosixTime(1281647191),
        CopyStringToTimestamp('2010-08-12 21:06:31'))

    self.assertEquals(
        timelib.Timestamp.FromPosixTime(-122557518),
        timelib.Timestamp.FromTimeString('1966-02-12 1966 12:14:42 UTC'))

    # POSIX time that exceeds upper bound.
    self.assertEquals(timelib.Timestamp.FromPosixTime(9223372036855), 0)

    # POSIX time that exceeds lower bound.
    self.assertEquals(timelib.Timestamp.FromPosixTime(-9223372036855), 0)

  def testMonthDict(self):
    """Test the month dict, both inside and outside of scope."""
    self.assertEquals(timelib.MONTH_DICT['nov'], 11)
    self.assertEquals(timelib.MONTH_DICT['jan'], 1)
    self.assertEquals(timelib.MONTH_DICT['may'], 5)

    month = timelib.MONTH_DICT.get('doesnotexist')
    self.assertEquals(month, None)

  def testLocaltimeToUTC(self):
    """Test the localtime to UTC conversion."""
    timezone = pytz.timezone('CET')

    local_timestamp = CopyStringToTimestamp('2013-01-01 01:00:00')
    self.assertEquals(
        timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone),
        CopyStringToTimestamp('2013-01-01 00:00:00'))

    local_timestamp = CopyStringToTimestamp('2013-07-01 02:00:00')
    self.assertEquals(
        timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone),
        CopyStringToTimestamp('2013-07-01 00:00:00'))

    # In the local timezone this is a non-existent timestamp.
    local_timestamp = CopyStringToTimestamp('2013-03-31 02:00:00')
    with self.assertRaises(pytz.NonExistentTimeError):
      timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone, is_dst=None)

    self.assertEquals(
        timelib.Timestamp.LocaltimeToUTC(
            local_timestamp, timezone, is_dst=True),
        CopyStringToTimestamp('2013-03-31 00:00:00'))

    self.assertEquals(
        timelib.Timestamp.LocaltimeToUTC(
            local_timestamp, timezone, is_dst=False),
        CopyStringToTimestamp('2013-03-31 01:00:00'))

    # In the local timezone this is an ambiguous timestamp.
    local_timestamp = CopyStringToTimestamp('2013-10-27 02:30:00')

    with self.assertRaises(pytz.AmbiguousTimeError):
      timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone, is_dst=None)

    self.assertEquals(
        timelib.Timestamp.LocaltimeToUTC(
            local_timestamp, timezone, is_dst=True),
        CopyStringToTimestamp('2013-10-27 00:30:00'))

    self.assertEquals(
        timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone),
        CopyStringToTimestamp('2013-10-27 01:30:00'))

    # Use the UTC timezone.
    self.assertEquals(
        timelib.Timestamp.LocaltimeToUTC(local_timestamp, pytz.utc),
        local_timestamp)

    # Use a timezone in the Western Hemisphere.
    timezone = pytz.timezone('EST')

    local_timestamp = CopyStringToTimestamp('2013-01-01 00:00:00')
    self.assertEquals(
        timelib.Timestamp.LocaltimeToUTC(local_timestamp, timezone),
        CopyStringToTimestamp('2013-01-01 05:00:00'))

  def testCopyToDatetime(self):
    """Test the copy to datetime object."""
    timezone = pytz.timezone('CET')

    timestamp = CopyStringToTimestamp('2013-03-14 20:20:08.850041')
    self.assertEquals(
        timelib.Timestamp.CopyToDatetime(timestamp, timezone),
        datetime.datetime(2013, 3, 14, 21, 20, 8, 850041, tzinfo=timezone))

  def testCopyToPosix(self):
    """Test converting microseconds to seconds."""
    timestamp = CopyStringToTimestamp('2013-10-01 12:00:00')
    self.assertEquals(
        timelib.Timestamp.CopyToPosix(timestamp),
        timestamp // 1000000)

  def testTimestampFromTimeString(self):
    """The the FromTimeString function."""
    # Test daylight savings.
    expected_timestamp = CopyStringToTimestamp('2013-10-01 12:00:00')

    # Check certain variance of this timestamp.
    timestamp = timelib.Timestamp.FromTimeString(
        '2013-10-01 14:00:00', pytz.timezone('Europe/Rome'))
    self.assertEquals(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        '2013-10-01 12:00:00', pytz.timezone('UTC'))
    self.assertEquals(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        '2013-10-01 05:00:00', pytz.timezone('PST8PDT'))
    self.assertEquals(timestamp, expected_timestamp)

    # Now to test outside of the daylight savings.
    expected_timestamp = CopyStringToTimestamp('2014-02-01 12:00:00')

    timestamp = timelib.Timestamp.FromTimeString(
        '2014-02-01 13:00:00', pytz.timezone('Europe/Rome'))
    self.assertEquals(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        '2014-02-01 12:00:00', pytz.timezone('UTC'))
    self.assertEquals(timestamp, expected_timestamp)

    timestamp = timelib.Timestamp.FromTimeString(
        '2014-02-01 04:00:00', pytz.timezone('PST8PDT'))
    self.assertEquals(timestamp, expected_timestamp)

    # Define two timestamps, one being GMT and the other UTC.
    time_string_utc = 'Wed 05 May 2010 03:52:31 UTC'
    time_string_gmt = 'Wed 05 May 2010 03:52:31 GMT'

    timestamp_utc = timelib.Timestamp.FromTimeString(time_string_utc)
    timestamp_gmt = timelib.Timestamp.FromTimeString(time_string_gmt)

    # Test if these two are different, and if so, then we'll try again
    # using the 'gmt_is_utc' flag, which then should result to the same
    # results.
    if timestamp_utc != timestamp_gmt:
      self.assertEquals(timestamp_utc, timelib.Timestamp.FromTimeString(
          time_string_gmt, gmt_as_timezone=False))

  def testRoundTimestamp(self):
    """Test the RoundToSeconds function."""
    # Should be rounded up.
    test_one = 442813351785412
    # Should be rounded down.
    test_two = 1384381247271976

    self.assertEquals(
        timelib.Timestamp.RoundToSeconds(test_one), 442813352000000)
    self.assertEquals(
        timelib.Timestamp.RoundToSeconds(test_two), 1384381247000000)

  def testTimestampFromTimeParts(self):
    """Test the FromTimeParts function."""
    timestamp = timelib.Timestamp.FromTimeParts(
        2013, 6, 25, 22, 19, 46, 0, timezone=pytz.timezone('PST8PDT'))
    self.assertEquals(
        timestamp, CopyStringToTimestamp('2013-06-25 22:19:46-07:00'))

    timestamp = timelib.Timestamp.FromTimeParts(2013, 6, 26, 5, 19, 46)
    self.assertEquals(
        timestamp, CopyStringToTimestamp('2013-06-26 05:19:46'))

    timestamp = timelib.Timestamp.FromTimeParts(
        2013, 6, 26, 5, 19, 46, 542)
    self.assertEquals(
        timestamp, CopyStringToTimestamp('2013-06-26 05:19:46.000542'))

  def _TestStringToDatetime(
      self, expected_timestamp, time_string, timezone=pytz.utc, dayfirst=False):
    """Tests the StringToDatetime function.

    Args:
      expected_timestamp: The expected timesamp.
      time_string: String that contains a date and time value.
      timezone: The timezone (pytz.timezone) object.
      dayfirst: Change precedence of day vs. month.

    Returns:
      A result object.
    """
    date_time = timelib.StringToDatetime(
        time_string, timezone=timezone, dayfirst=dayfirst)
    timestamp = int(calendar.timegm((date_time.utctimetuple())))
    self.assertEquals(timestamp, expected_timestamp)

  def testStringToDatetime(self):
    """Test the StringToDatetime function."""
    self._TestStringToDatetime(
        471953580, '12-15-1984 05:13:00', timezone=pytz.timezone('EST5EDT'))

    # Swap day and month.
    self._TestStringToDatetime(
        466420380, '12-10-1984 05:13:00', timezone=pytz.timezone('EST5EDT'),
        dayfirst=True)

    self._TestStringToDatetime(471953580, '12-15-1984 10:13:00Z')

    # Setting the timezone for string that already contains a timezone
    # indicator should not affect the conversion.
    self._TestStringToDatetime(
        471953580, '12-15-1984 10:13:00Z', timezone=pytz.timezone('EST5EDT'))

    self._TestStringToDatetime(471953580, '15/12/1984 10:13:00Z')

    self._TestStringToDatetime(471953580, '15-12-84 10:13:00Z')

    self._TestStringToDatetime(
        471967980, '15-12-84 10:13:00-04', timezone=pytz.timezone('EST5EDT'))

    self._TestStringToDatetime(
        0, 'thisisnotadatetime', timezone=pytz.timezone('EST5EDT'))

    self._TestStringToDatetime(
        471953580, '12-15-1984 04:13:00',
        timezone=pytz.timezone('America/Chicago'))

    self._TestStringToDatetime(
        458712780, '07-14-1984 23:13:00',
        timezone=pytz.timezone('America/Chicago'))

    self._TestStringToDatetime(
        471964380, '12-15-1984 05:13:00', timezone=pytz.timezone('US/Pacific'))


if __name__ == '__main__':
  unittest.main()
