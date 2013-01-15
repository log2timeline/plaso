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
"""This file contains functions and variables used for time manipulations.

This file should contain common methods that can be used in Plaso to convert
timestamps in various formats into the standard micro seconds precision integer
Epoch UTC time that is used internally to store timestamps in Plaso.

The file can also contain common functions to change the default timestamp into
a more human readable one.
"""
import calendar
import datetime
import pytz

MONTH_DICT = {
    'jan': 1,
    'feb': 2,
    'mar': 3,
    'apr': 4,
    'may': 5,
    'jun': 6,
    'jul': 7,
    'aug': 8,
    'sep': 9,
    'oct': 10,
    'nov': 11,
    'dec': 12}


class Timestamp(object):
  """The Plaso timestamp is a 64-bit signed timestamp value containing:
     micro seconds since 1970-01-01 00:00:00.

     The timestamp is not necessarily in UTC.
  """
  # The minimum timestamp in seconds
  TIMESTAMP_MIN_SECONDS = -(((1 << 63L) - 1) / 1000000)

  # The maximum timestamp in seconds
  TIMESTAMP_MAX_SECONDS = ((1 << 63L) - 1) / 1000000

  # The maximum timestamp in micro seconds
  TIMESTAMP_MAX_MICRO_SECONDS = (1 << 63L) - 1

  # The days per month of a non leap year
  DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

  # The number of seconds in a day
  SECONDS_PER_DAY = 24 * 60 * 60

  # The number of micro seconds per second
  MICRO_SECONDS_PER_SECOND = 1000000

  # The difference between Jan 1, 1980 and Jan 1, 1970 in seconds.
  FAT_DATE_TO_POSIX_BASE = 315532800

  # The difference between Jan 1, 1601 and Jan 1, 1970 in 100th of nano seconds.
  FILETIME_TO_POSIX_BASE = 11644473600L * 10000000

  __pychecker__ = 'unusednames=cls'
  @classmethod
  def IsLeapYear(cls, year):
    """Determines if a year is a leap year.

       A leap year is dividable by 4 and not by 100 or by 400
       without a remainder.

    Args:
      year: The year as in 1970.

    Returns:
      A boolean value indicating the year is a leap year.
    """
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0

  @classmethod
  def DaysInYear(cls, year):
    """Determines the days in a year.

    Args:
      year: The year as in 1970.

    Returns:
      An integer containing the number of days in the year.
    """
    days_in_year = 365
    if cls.IsLeapYear(year):
      return days_in_year + 1
    return days_in_year

  @classmethod
  def DaysInMonth(cls, month, year):
    """Determines the days in a month for a specific year.

    Args:
      month: The month where 0 represents January.
      year: The year as in 1970.

    Returns:
      An integer containing the number of days in the month.
    """
    days_per_month = cls.DAYS_PER_MONTH[month]

    if month == 1 and cls.IsLeapYear(year):
      days_per_month += 1

    return days_per_month

  @classmethod
  def DayOfYear(cls, day, month, year):
    """Determines the day of the year for a specific day of a month in a year.

    Args:
      day_of_month: The day of the month where 0 represents the first day.
      month: The month where 0 represents January.
      year: The year as in 1970.

    Returns:
      An integer containing the day of year.
    """
    day_of_year = day

    for past_month in range(0, month):
      day_of_year += cls.DaysInMonth(past_month, year)

    return day_of_year

  @classmethod
  def FromFatDateTime(cls, fat_date_time):
    """Converts a FAT date and time into a timestamp.

    FAT date time is mainly used in DOS/Windows file formats and NTFS.

    The FAT date and time is a 32-bit value containing two 16-bit values:
      * The time of day (lower 16-bit).
        * bits 0 - 4: seconds (in 2 second intervals)
        * bits 5 - 10: minutes
        * bits 11 - 15: hours
      * The date (upper 16-bit).
        * bits 0 - 4:  day of month, where 1 represents the first day
        * bits 5 - 8:  month of year, where 1 represent January
        * bits 9 - 15: year since 1980

    Args:
      fat_date_time: The 32-bit FAT date time.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    number_of_seconds = cls.FAT_DATE_TO_POSIX_BASE

    seconds = (fat_date_time & 0x1f) * 2
    minutes = (fat_date_time >> 5) & 0x3f
    hours = (fat_date_time >> 11) & 0x1f

    if hours > 23 or minutes > 59 or seconds > 59:
      return 0

    number_of_seconds += (((hours * 60) + minutes) * 60) + seconds

    fat_date_time >>= 16
    day_of_month = (fat_date_time & 0x1f) - 1
    month = ((fat_date_time >> 5) & 0x0f) - 1
    year = (fat_date_time >> 9) & 0x7f

    if day_of_month < 0 or day_of_month > 30 or month < 0 or month > 11:
      return 0

    number_of_days = cls.DayOfYear(day_of_month, month, 1980 + year)
    for past_year in range(0, year):
      number_of_days += cls.DaysInYear(past_year)

    number_of_seconds += number_of_days * cls.SECONDS_PER_DAY

    return number_of_seconds * cls.MICRO_SECONDS_PER_SECOND

  @classmethod
  def FromFiletime(cls, filetime):
    """Converts a FILETIME into a timestamp.

    FILETIME is mainly used in Windows file formats and NTFS.

    The FILETIME is a 64-bit value containing:
      100th nano seconds since 1601-01-01 00:00:00

    Technically FILETIME consists of 2 x 32-bit parts and is presumed
    to be unsigned.

    Args:
      filetime: The 64-bit FILETIME timestamp.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    if filetime < 0:
      return 0
    timestamp = (filetime - cls.FILETIME_TO_POSIX_BASE) / 10

    if timestamp > cls.TIMESTAMP_MAX_MICRO_SECONDS:
      return 0
    return timestamp

  @classmethod
  def FromPosixTime(cls, posix_time):
    """Converts a POSIX timestamp into a timestamp.

    The POSIX time is a signed 32-bit or 64-bit value containing:
      seconds since 1970-01-01 00:00:00

    Args:
      posix_time: The POSIX timestamp.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    if (posix_time < cls.TIMESTAMP_MIN_SECONDS or
        posix_time > cls.TIMESTAMP_MAX_SECONDS):
      return 0
    return posix_time * cls.MICRO_SECONDS_PER_SECOND


def Timetuple2Timestamp(time_tuple):
  """Return a micro second precision timestamp from a timetuple."""
  if type(time_tuple) != tuple:
    return 0

  return int(calendar.timegm(time_tuple))


def DateTimeFromTimestamp(timestamp, zone):
  """Return a datetime object from a given timestamp."""
  try:
    mydate = datetime.datetime.utcfromtimestamp(
        timestamp / 1e6)
  except ValueError:
     return None

  return mydate.replace(tzinfo=pytz.utc).astimezone(zone)
