# -*- coding: utf-8 -*-
"""Time manipulation functions and variables.

This module contain common methods that can be used to convert timestamps
from various formats into number of micro seconds since January 1, 1970,
00:00:00 UTC that is used internally to store timestamps.

It also contains various functions to represent timestamps in a more
human readable form.
"""

from __future__ import unicode_literals

import calendar
import datetime
import logging
import time

import dateutil.parser
import pytz

from plaso.lib import errors
from plaso.lib import py2to3


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
  """Class for converting timestamps to plaso timestamps.

    The Plaso timestamp is a 64-bit signed timestamp value containing:
    micro seconds since 1970-01-01 00:00:00.

    The timestamp is not necessarily in UTC.
  """
  # The minimum timestamp in seconds
  TIMESTAMP_MIN_SECONDS = -(((1 << 63) - 1) / 1000000)

  # The maximum timestamp in seconds
  TIMESTAMP_MAX_SECONDS = ((1 << 63) - 1) / 1000000

  # The minimum timestamp in micro seconds
  TIMESTAMP_MIN_MICRO_SECONDS = -((1 << 63) - 1)

  # The maximum timestamp in micro seconds
  TIMESTAMP_MAX_MICRO_SECONDS = (1 << 63) - 1

  # Timestamp that represents the timestamp representing not
  # a date and time value.
  # TODO: replace this with a real None implementation.
  NONE_TIMESTAMP = 0

  # The days per month of a non leap year
  DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

  # The number of micro seconds per second
  MICRO_SECONDS_PER_SECOND = 1000000

  # The multiplication factor to change milliseconds to micro seconds.
  MILLI_SECONDS_TO_MICRO_SECONDS = 1000

  @classmethod
  def CopyFromString(cls, time_string):
    """Copies a timestamp from a string containing a date and time value.

    Args:
      time_string: A string containing a date and time value formatted as:
                   YYYY-MM-DD hh:mm:ss.######[+-]##:##
                   Where # are numeric digits ranging from 0 to 9 and the
                   seconds fraction can be either 3 or 6 digits. The time
                   of day, seconds fraction and timezone offset are optional.
                   The default timezone is UTC.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC.

    Raises:
      ValueError: if the time string is invalid or not supported.
    """
    if not time_string:
      raise ValueError('Invalid time string.')

    time_string_length = len(time_string)

    # The time string should at least contain 'YYYY-MM-DD'.
    if (time_string_length < 10 or time_string[4] != '-' or
        time_string[7] != '-'):
      raise ValueError('Invalid time string.')

    # If a time of day is specified the time string it should at least
    # contain 'YYYY-MM-DD hh:mm:ss'.
    if (time_string_length > 10 and (
        time_string_length < 19 or time_string[10] != ' ' or
        time_string[13] != ':' or time_string[16] != ':')):
      raise ValueError('Invalid time string.')

    try:
      year = int(time_string[0:4], 10)
    except ValueError:
      raise ValueError('Unable to parse year.')

    try:
      month = int(time_string[5:7], 10)
    except ValueError:
      raise ValueError('Unable to parse month.')

    if month not in range(1, 13):
      raise ValueError('Month value out of bounds.')

    try:
      day_of_month = int(time_string[8:10], 10)
    except ValueError:
      raise ValueError('Unable to parse day of month.')

    if day_of_month not in range(1, 32):
      raise ValueError('Day of month value out of bounds.')

    hours = 0
    minutes = 0
    seconds = 0

    if time_string_length > 10:
      try:
        hours = int(time_string[11:13], 10)
      except ValueError:
        raise ValueError('Unable to parse hours.')

      if hours not in range(0, 24):
        raise ValueError('Hours value out of bounds.')

      try:
        minutes = int(time_string[14:16], 10)
      except ValueError:
        raise ValueError('Unable to parse minutes.')

      if minutes not in range(0, 60):
        raise ValueError('Minutes value out of bounds.')

      try:
        seconds = int(time_string[17:19], 10)
      except ValueError:
        raise ValueError('Unable to parse day of seconds.')

      if seconds not in range(0, 60):
        raise ValueError('Seconds value out of bounds.')

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
          raise ValueError('Invalid time string.')

        try:
          micro_seconds = int(time_string[20:timezone_index], 10)
        except ValueError:
          raise ValueError('Unable to parse fraction of seconds.')

        if fraction_of_seconds_length == 3:
          micro_seconds *= 1000

      if timezone_index < time_string_length:
        if (time_string_length - timezone_index != 6 or
            time_string[timezone_index + 3] != ':'):
          raise ValueError('Invalid time string.')

        try:
          timezone_offset = int(time_string[
              timezone_index + 1:timezone_index + 3])
        except ValueError:
          raise ValueError('Unable to parse timezone hours offset.')

        if timezone_offset not in range(0, 24):
          raise ValueError('Timezone hours offset value out of bounds.')

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
          raise ValueError('Unable to parse timezone minutes offset.')

        timezone_offset *= 60

    timestamp = int(calendar.timegm((
        year, month, day_of_month, hours, minutes, seconds)))

    return ((timestamp + timezone_offset) * 1000000) + micro_seconds

  @classmethod
  def CopyToDatetime(cls, timestamp, timezone, raise_error=False):
    """Copies the timestamp to a datetime object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timezone: The timezone (pytz.timezone) object.
      raise_error: Boolean that if set to True will not absorb an OverflowError
                   if the timestamp is out of bounds. By default there will be
                   no error raised.

    Returns:
      A datetime object (instance of datetime.datetime). A datetime object of
      January 1, 1970 00:00:00 UTC is returned on error if raises_error is
      not set.

    Raises:
      OverflowError: If raises_error is set to True and an overflow error
                     occurs.
    """
    datetime_object = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)
    try:
      datetime_object += datetime.timedelta(microseconds=timestamp)
      return datetime_object.astimezone(timezone)
    except OverflowError as exception:
      if raise_error:
        raise

      logging.error((
          'Unable to copy {0:d} to a datetime object with error: '
          '{1:s}').format(timestamp, exception))

    return datetime_object

  @classmethod
  def CopyToIsoFormat(cls, timestamp, timezone=pytz.UTC, raise_error=False):
    """Copies the timestamp to an ISO 8601 formatted string.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timezone: Optional timezone (instance of pytz.timezone).
      raise_error: Boolean that if set to True will not absorb an OverflowError
                   if the timestamp is out of bounds. By default there will be
                   no error raised.

    Returns:
      A string containing an ISO 8601 formatted date and time.
    """
    datetime_object = cls.CopyToDatetime(
        timestamp, timezone, raise_error=raise_error)
    return datetime_object.isoformat()

  @classmethod
  def CopyToPosix(cls, timestamp):
    """Converts microsecond timestamps to POSIX timestamps.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.

    Returns:
      The timestamp which is an integer containing the number of seconds
      since January 1, 1970, 00:00:00 UTC.
    """
    return timestamp // cls.MICRO_SECONDS_PER_SECOND

  @classmethod
  def DaysInMonth(cls, month, year):
    """Determines the days in a month for a specific year.

    Args:
      month: The month where 0 represents January.
      year: The year as in 1970.

    Returns:
      An integer containing the number of days in the month.

    Raises:
      ValueError: if the month value is invalid.
    """
    if month not in range(0, 12):
      raise ValueError('Invalid month value')

    days_per_month = cls.DAYS_PER_MONTH[month]

    if month == 1 and cls.IsLeapYear(year):
      days_per_month += 1

    return days_per_month

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
  def DayOfYear(cls, day, month, year):
    """Determines the day of the year for a specific day of a month in a year.

    Args:
      day: The day of the month where 0 represents the first day.
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
  def FromPosixTime(cls, posix_time):
    """Converts a POSIX timestamp into a timestamp.

    The POSIX time is a signed 32-bit or 64-bit value containing:
      seconds since 1970-01-01 00:00:00

    Args:
      posix_time: The POSIX timestamp.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC or 0 on error.
    """
    if (posix_time < cls.TIMESTAMP_MIN_SECONDS or
        posix_time > cls.TIMESTAMP_MAX_SECONDS):
      return 0
    return int(posix_time) * cls.MICRO_SECONDS_PER_SECOND

  @classmethod
  def FromPosixTimeWithMicrosecond(cls, posix_time, microsecond):
    """Converts a POSIX timestamp with microsecond into a timestamp.

    The POSIX time is a signed 32-bit or 64-bit value containing:
      seconds since 1970-01-01 00:00:00

    Args:
      posix_time: The POSIX timestamp.
      microsecond: The microseconds to add to the timestamp.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC or 0 on error.
    """
    timestamp = cls.FromPosixTime(posix_time)
    if not timestamp:
      return 0
    return timestamp + microsecond

  @classmethod
  def FromPythonDatetime(cls, datetime_object):
    """Converts a Python datetime object into a timestamp.

    Args:
      datetime_object: The datetime object (instance of datetime.datetime).

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC or 0 on error.
    """
    if not isinstance(datetime_object, datetime.datetime):
      return 0

    posix_time = int(calendar.timegm(datetime_object.utctimetuple()))
    return cls.FromPosixTime(posix_time) + datetime_object.microsecond

  @classmethod
  def FromRFC2579Datetime(
      cls, year, month, day, hour, minutes, seconds, deciseconds,
      direction_from_utc, hours_from_utc, minutes_from_utc):
    """Converts values from an RFC2579 time to a timestamp.

    See https://tools.ietf.org/html/rfc2579.

    Args:
      year: An integer representing the year.
      month: An integer between 1 and 12.
      day: An integer representing the number of day in the month.
      hour: An integer representing the hour, 0 <= hour < 24.
      minutes: An integer, 0 <= minute < 60.
      seconds: An integer, 0 <= second < 60.
      deciseconds: An integer, 0 <= deciseconds < 10
      direction_from_utc: An ascii character, either '+' or '-'.
      hours_from_utc: An integer representing the number of hours the time is
                      offset from UTC.
      minutes_from_utc: An integer representing the number of seconds the time
                        is offset from UTC.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC or 0 on error.

    Raises:
      TimestampError: if the timestamp cannot be created from the time parts.
    """
    microseconds = deciseconds * 100000
    utc_offset_minutes = (hours_from_utc * 60) + minutes_from_utc
    if direction_from_utc == '-':
      utc_offset_minutes = -utc_offset_minutes
    timezone = pytz.FixedOffset(utc_offset_minutes)
    return cls.FromTimeParts(
        year, month, day, hour, minutes, seconds, microseconds, timezone)

  @classmethod
  def FromTimeParts(
      cls, year, month, day, hour, minutes, seconds, microseconds=0,
      timezone=pytz.UTC):
    """Converts a list of time entries to a timestamp.

    Args:
      year: An integer representing the year.
      month: An integer between 1 and 12.
      day: An integer representing the number of day in the month.
      hour: An integer representing the hour, 0 <= hour < 24.
      minutes: An integer, 0 <= minute < 60.
      seconds: An integer, 0 <= second < 60.
      microseconds: Optional number of microseconds ranging from:
                    0 <= microsecond < 1000000.
      timezone: Optional timezone (instance of pytz.timezone).

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC or 0 on error.

    Raises:
      TimestampError: if the timestamp cannot be created from the time parts.
    """
    try:
      date = datetime.datetime(
          year, month, day, hour, minutes, seconds, microseconds)
    except ValueError as exception:
      raise errors.TimestampError((
          'Unable to create timestamp from {0:04d}-{1:02d}-{2:02d} '
          '{3:02d}:{4:02d}:{5:02d}.{6:06d} with error: {7!s}').format(
              year, month, day, hour, minutes, seconds, microseconds,
              exception))

    if isinstance(timezone, py2to3.STRING_TYPES):
      timezone = pytz.timezone(timezone)

    date_use = timezone.localize(date)
    posix_time = int(calendar.timegm(date_use.utctimetuple()))

    return cls.FromPosixTime(posix_time) + microseconds

  @classmethod
  def FromTimeString(
      cls, time_string, dayfirst=False, gmt_as_timezone=True,
      timezone=pytz.UTC):
    """Converts a string containing a date and time value into a timestamp.

    Args:
      time_string: String that contains a date and time value.
      dayfirst: An optional boolean argument. If set to true then the
                parser will change the precedence in which it parses timestamps
                from MM-DD-YYYY to DD-MM-YYYY (and YYYY-MM-DD will be
                YYYY-DD-MM, etc).
      gmt_as_timezone: Sometimes the dateutil parser will interpret GMT and UTC
                       the same way, that is not make a distinction. By default
                       this is set to true, that is GMT can be interpreted
                       differently than UTC. If that is not the expected result
                       this attribute can be set to false.
      timezone: Optional timezone object (instance of pytz.timezone) that
                the data and time value in the string represents. This value
                is used when the timezone cannot be determined from the string.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC or 0 on error.

    Raises:
      TimestampError: if the time string could not be parsed.
    """
    if not gmt_as_timezone and time_string.endswith(' GMT'):
      time_string = '{0:s}UTC'.format(time_string[:-3])

    try:
      # TODO: deprecate the use of dateutil parser.
      datetime_object = dateutil.parser.parse(time_string, dayfirst=dayfirst)

    except (TypeError, ValueError) as exception:
      raise errors.TimestampError((
          'Unable to convert time string: {0:s} in to a datetime object '
          'with error: {1!s}').format(time_string, exception))

    if datetime_object.tzinfo:
      datetime_object = datetime_object.astimezone(pytz.UTC)
    else:
      datetime_object = timezone.localize(datetime_object)

    return cls.FromPythonDatetime(datetime_object)

  @classmethod
  def GetNow(cls):
    """Retrieves the current time (now) as a timestamp in UTC.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC.
    """
    time_elements = time.gmtime()
    return calendar.timegm(time_elements) * 1000000

  @classmethod
  def IsLeapYear(cls, year):
    """Determines if a year is a leap year.

       A leap year is divisible by 4 and not by 100 or by 400.

    Args:
      year: The year as in 1970.

    Returns:
      A boolean value indicating the year is a leap year.
    """
    # pylint: disable=consider-using-ternary
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0

  @classmethod
  def LocaltimeToUTC(cls, timestamp, timezone, is_dst=False):
    """Converts the timestamp in localtime of the timezone to UTC.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timezone: The timezone (pytz.timezone) object.
      is_dst: A boolean to indicate the timestamp is corrected for daylight
              savings time (DST) only used for the DST transition period.

    Returns:
      The timestamp which is an integer containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC or 0 on error.
    """
    if timezone and timezone != pytz.UTC:
      datetime_object = (
          datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=None) +
          datetime.timedelta(microseconds=timestamp))

      # Check if timezone is UTC since utcoffset() does not support is_dst
      # for UTC and will raise.
      datetime_delta = timezone.utcoffset(datetime_object, is_dst=is_dst)
      seconds_delta = int(datetime_delta.total_seconds())
      timestamp -= seconds_delta * cls.MICRO_SECONDS_PER_SECOND

    return timestamp

  @classmethod
  def RoundToSeconds(cls, timestamp):
    """Takes a timestamp value and rounds it to a second precision."""
    leftovers = timestamp % cls.MICRO_SECONDS_PER_SECOND
    scrubbed = timestamp - leftovers
    rounded = round(float(leftovers) / cls.MICRO_SECONDS_PER_SECOND)

    return int(scrubbed + rounded * cls.MICRO_SECONDS_PER_SECOND)


def GetCurrentYear():
  """Determines the current year."""
  datetime_object = datetime.datetime.now()
  return datetime_object.year


def GetYearFromPosixTime(posix_time, timezone=pytz.UTC):
  """Gets the year from a POSIX timestamp

  The POSIX time is the number of seconds since 1970-01-01 00:00:00 UTC.

  Args:
    posix_time: An integer containing the number of seconds since
                1970-01-01 00:00:00 UTC.
    timezone: Optional timezone of the POSIX timestamp.

  Returns:
    The year of the POSIX timestamp.

  Raises:
    ValueError: If the posix timestamp is out of the range of supported values.
  """
  datetime_object = datetime.datetime.fromtimestamp(posix_time, tz=timezone)
  return datetime_object.year
