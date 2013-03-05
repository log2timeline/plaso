#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains a unit test for the timelib in Plaso."""
import unittest

from plaso.lib import timelib


class TimeLibUnitTest(unittest.TestCase):
  """A unit test for the timelib."""

  def testTimestampIsLeapYear(self):
    """Test the is leap year check."""
    self.assertEquals(timelib.Timestamp.IsLeapYear(2012), True)
    self.assertEquals(timelib.Timestamp.IsLeapYear(2013), False)
    self.assertEquals(timelib.Timestamp.IsLeapYear(2000), True)
    self.assertEquals(timelib.Timestamp.IsLeapYear(1900), False)

  def testTimestampDaysInMonth(self):
    """Test the days in month function."""
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

  def testTimestampFromFatDateTime(self):
    """Test the FAT date time conversion."""
    # Aug 12, 2010 21:06:32
    fat_date_time = 0xa8d03d0c
    # date -u -d"Aug 12, 2010 21:06:32" +"%s"
    timestamp = 1281647192 * 1000000
    self.assertEquals(
        timelib.Timestamp.FromFatDateTime(fat_date_time), timestamp)

    # Invalid number of seconds.
    fat_date_time = (0xa8d03d0c & ~(0x1f << 16)) | ((30 & 0x1f) << 16)
    self.assertEquals(
        timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid number of minutes.
    fat_date_time = (0xa8d03d0c & ~(0x3f << 21)) | ((60 & 0x3f) << 21)
    self.assertEquals(
        timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid number of hours.
    fat_date_time = (0xa8d03d0c & ~(0x1f << 27)) | ((24 & 0x1f) << 27)
    self.assertEquals(
        timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid day of month.
    fat_date_time = (0xa8d03d0c & ~(0x1f)) | (32 & 0x1f)
    self.assertEquals(
        timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

    # Invalid month.
    fat_date_time = (0xa8d03d0c & ~(0x0f << 5)) | ((13 & 0x0f) << 5)
    self.assertEquals(
        timelib.Timestamp.FromFatDateTime(fat_date_time), 0)

  def testTimestampFromWebKitTime(self):
    """Test the WebKit time conversion."""
    # Aug 12, 2010 21:06:31.546875000
    # date -u -d"Aug 12, 2010 21:06:31.546875000" +"%s.%N"
    webkit_time = 0x2dec3d061a9bfb
    timestamp = (1281647191 * 1000000) + int(546875000 / 1000)
    self.assertEquals(timelib.Timestamp.FromWebKitTime(webkit_time), timestamp)

    # Jan 2, 1601 00:00:00.000000000
    # date -u -d"Jan 2, 1601 00:00:00.000000000" +"%s.%N"
    webkit_time = 86400 * 1000000
    timestamp = (-11644387200 * 1000000)
    self.assertEquals(timelib.Timestamp.FromWebKitTime(webkit_time), timestamp)

    # WebKit time that exceeds lower bound.
    webkit_time = -((1 << 63L) - 1)
    self.assertEquals(timelib.Timestamp.FromWebKitTime(webkit_time), 0)

  def testTimestampFromFiletime(self):
    """Test the FILETIME conversion."""
    # Aug 12, 2010 21:06:31.546875000
    # date -u -d"Aug 12, 2010 21:06:31.546875000" +"%s.%N"
    filetime = 0x01cb3a623d0a17ce
    timestamp = (1281647191 * 1000000) + int(546875000 / 1000)
    self.assertEquals(timelib.Timestamp.FromFiletime(filetime), timestamp)

    # Jan 2, 1601 00:00:00.000000000
    # date -u -d"Jan 2, 1601 00:00:00.000000000" +"%s.%N"
    filetime = 86400 * 10000000
    timestamp = (-11644387200 * 1000000)
    self.assertEquals(timelib.Timestamp.FromFiletime(filetime), timestamp)

    # FILETIME that exceeds lower bound.
    filetime = -1
    self.assertEquals(timelib.Timestamp.FromFiletime(filetime), 0)

  def testTimestampFromPosixTIme(self):
    """Test the POSIX time conversion."""
    # Aug 12, 2010 21:06:31.546875000
    # date -u -d"Aug 12, 2010 21:06:31" +"%s"
    posix_time = 1281647191
    timestamp = 1281647191 * 1000000
    self.assertEquals(timelib.Timestamp.FromPosixTime(posix_time), timestamp)

    # Feb 12, 1966 12:14:42
    # date -u -d"Feb 12, 1966 12:14:42" +"%s"
    posix_time = -122557518
    timestamp = -122557518 * 1000000
    self.assertEquals(timelib.Timestamp.FromPosixTime(posix_time), timestamp)

    # POSIX time that exceeds upper bound.
    posix_time = 9223372036855
    self.assertEquals(timelib.Timestamp.FromPosixTime(posix_time), 0)

    # POSIX time that exceeds lower bound.
    posix_time = -9223372036855
    self.assertEquals(timelib.Timestamp.FromPosixTime(posix_time), 0)

  def testMonthDict(self):
    """Test the month dict, both inside and outside of scope."""
    self.assertEquals(timelib.MONTH_DICT['nov'], 11)
    self.assertEquals(timelib.MONTH_DICT['jan'], 1)
    self.assertEquals(timelib.MONTH_DICT['may'], 5)

    month = timelib.MONTH_DICT.get('doesnotexist')
    self.assertEquals(month, None)


if __name__ == '__main__':
  unittest.main()
