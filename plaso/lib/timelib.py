# -*- coding: utf-8 -*-
"""This file contains functions and variables used for time manipulations.

This file should contain common methods that can be used in Plaso to convert
timestamps in various formats into the standard micro seconds precision integer
Epoch UTC time that is used internally to store timestamps in Plaso.

The file can also contain common functions to change the default timestamp into
a more human readable one.
"""

import calendar
import datetime
import dateutil.parser
import logging
import time
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
  """Class for converting timestamps to plaso timestamps.

    The Plaso timestamp is a 64-bit signed timestamp value containing:
    micro seconds since 1970-01-01 00:00:00.

    The timestamp is not necessarily in UTC.
  """
  # The minimum timestamp in seconds
  TIMESTAMP_MIN_SECONDS = -(((1 << 63L) - 1) / 1000000)

  # The maximum timestamp in seconds
  TIMESTAMP_MAX_SECONDS = ((1 << 63L) - 1) / 1000000

  # The minimum timestamp in micro seconds
  TIMESTAMP_MIN_MICRO_SECONDS = -((1 << 63L) - 1)

  # The maximum timestamp in micro seconds
  TIMESTAMP_MAX_MICRO_SECONDS = (1 << 63L) - 1

  # The days per month of a non leap year
  DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

  # The number of seconds in a day
  SECONDS_PER_DAY = 24 * 60 * 60

  # The number of micro seconds per second
  MICRO_SECONDS_PER_SECOND = 1000000

  # The multiplication factor to change milli seconds to micro seconds.
  MILLI_SECONDS_TO_MICRO_SECONDS = 1000

  # The difference between Jan 1, 1980 and Jan 1, 1970 in seconds.
  FAT_DATE_TO_POSIX_BASE = 315532800

  # The difference between Jan 1, 1601 and Jan 1, 1970 in micro seconds
  WEBKIT_TIME_TO_POSIX_BASE = 11644473600L * 1000000

  # The difference between Jan 1, 1601 and Jan 1, 1970 in 100s of nanoseconds.
  FILETIME_TO_POSIX_BASE = 11644473600L * 10000000

  # The number of seconds between January 1, 1904 and Jan 1, 1970.
  # Value confirmed with sleuthkit:
  #  http://svn.sleuthkit.org/repos/sleuthkit/trunk/tsk3/fs/tsk_hfs.h
  # and linux source file linux/include/linux/hfsplus_fs.h
  HFSTIME_TO_POSIX_BASE = 2082844800

  # The number of seconds between January 1, 1970 and January 1, 2001.
  # As specified in:
  # https://developer.apple.com/library/ios/documentation/
  #       cocoa/Conceptual/DatesAndTimes/Articles/dtDates.html
  COCOA_TIME_TO_POSIX_BASE = 978307200

  # The difference between POSIX (Jan 1, 1970) and DELPHI (Dec 30, 1899).
  # http://docwiki.embarcadero.com/Libraries/XE3/en/System.TDateTime
  DELPHI_TIME_TO_POSIX_BASE = 25569

  @classmethod
  def CopyToDatetime(cls, timestamp, timezone, raise_error=False):
    """Copies the timestamp to a datetime object.

    Args:
      timestamp: An integer containing the timestamp.
      timezone: The timezone (pytz.timezone) object.
      raise_error: Boolean that if set to True will not absorb an OverflowError
                   if the timestamp is out of bounds. By default there will be
                   no error raised.

    Returns:
      A datetime object.

    Raises:
      OverflowError: If raises_error is set to True and an OverflowError error
                     occurs. Otherwise the error is absorbed and a datetime
                     object from the beginning of UNIX Epoch is returned.
    """
    datetime_object = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=pytz.utc)
    try:
      datetime_object += datetime.timedelta(microseconds=timestamp)
      return datetime_object.astimezone(timezone)
    except OverflowError as exception:
      if raise_error:
        raise
      else:
        logging.error((
            u'Unable to copy {0:d} to a datetime object with error: '
            u'{1:s}').format(timestamp, exception))

    return datetime_object

  @classmethod
  def CopyToIsoFormat(cls, timestamp, timezone=pytz.utc, raise_error=False):
    """Copies the timestamp to an ISO 8601 formatted string.

    Args:
      timestamp: An integer containing the timestamp.
      timezone: Optional timezone (instance of pytz.timezone).
                The default is UTC.
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
      timestamp: An integer containing the microsecond timestamp.

    Returns:
      An integer value containing the timestamp.
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
      raise ValueError(u'Invalid month value')

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
  def FromCocoaTime(cls, cocoa_time):
    """Converts a Cocoa time to a timestamp.

    In Cocoa, time and date values are stored in a unsigned 32-bit integer
    containing the number of seconds since January 1, 2001 at 00:00:00
    (midnight) UTC (GMT).

    Args:
      cocoa_time: The timestamp in Cocoa format.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    return cls.FromPosixTime(cocoa_time + cls.COCOA_TIME_TO_POSIX_BASE)

  @classmethod
  def FromDelphiTime(cls, delphi_time):
    """Converts a Delphi time to a timestamp.

    In Delphi, time and date values (TDateTime)
    are stored in a unsigned little endian 64-bit
    floating point containing the number of seconds
    since December 30, 1899 at 00:00:00 (midnight) Local Timezone.
    TDateTime does not have any time zone information.

    Args:
      delphi_time: The timestamp in Delphi format.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    posix_time = (delphi_time - cls.DELPHI_TIME_TO_POSIX_BASE) * 86400.0
    if (posix_time < cls.TIMESTAMP_MIN_SECONDS or
        posix_time > cls.TIMESTAMP_MAX_SECONDS):
      return 0

    return cls.FromPosixTime(int(posix_time))

  @classmethod
  def FromFatDateTime(cls, fat_date_time):
    """Converts a FAT date and time into a timestamp.

    FAT date time is mainly used in DOS/Windows file formats and FAT.

    The FAT date and time is a 32-bit value containing two 16-bit values:
      * The date (lower 16-bit).
        * bits 0 - 4:  day of month, where 1 represents the first day
        * bits 5 - 8:  month of year, where 1 represent January
        * bits 9 - 15: year since 1980
      * The time of day (upper 16-bit).
        * bits 0 - 4: seconds (in 2 second intervals)
        * bits 5 - 10: minutes
        * bits 11 - 15: hours

    Args:
      fat_date_time: The 32-bit FAT date time.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    number_of_seconds = cls.FAT_DATE_TO_POSIX_BASE

    day_of_month = (fat_date_time & 0x1f) - 1
    month = ((fat_date_time >> 5) & 0x0f) - 1
    year = (fat_date_time >> 9) & 0x7f

    if day_of_month < 0 or day_of_month > 30 or month < 0 or month > 11:
      return 0

    number_of_days = cls.DayOfYear(day_of_month, month, 1980 + year)
    for past_year in range(0, year):
      number_of_days += cls.DaysInYear(past_year)

    fat_date_time >>= 16

    seconds = (fat_date_time & 0x1f) * 2
    minutes = (fat_date_time >> 5) & 0x3f
    hours = (fat_date_time >> 11) & 0x1f

    if hours > 23 or minutes > 59 or seconds > 59:
      return 0

    number_of_seconds += (((hours * 60) + minutes) * 60) + seconds

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
    # TODO: Add a handling for if the timestamp equals to zero.
    if filetime < 0:
      return 0
    timestamp = (filetime - cls.FILETIME_TO_POSIX_BASE) / 10

    if timestamp > cls.TIMESTAMP_MAX_MICRO_SECONDS:
      return 0
    return timestamp

  @classmethod
  def FromHfsTime(cls, hfs_time, timezone=pytz.utc, is_dst=False):
    """Converts a HFS time to a timestamp.

    HFS time is the same as HFS+ time, except stored in the local
    timezone of the user.

    Args:
      hfs_time: Timestamp in the hfs format (32 bit unsigned int).
      timezone: The timezone object of the system's local time.
      is_dst: A boolean to indicate the timestamp is corrected for daylight
              savings time (DST) only used for the DST transition period.
              The default is false.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    timestamp_local = cls.FromHfsPlusTime(hfs_time)
    return cls.LocaltimeToUTC(timestamp_local, timezone, is_dst)

  @classmethod
  def FromHfsPlusTime(cls, hfs_time):
    """Converts a HFS+ time to a timestamp.

    In HFS+ date and time values are stored in an unsigned 32-bit integer
    containing the number of seconds since January 1, 1904 at 00:00:00
    (midnight) UTC (GMT).

    Args:
      hfs_time: The timestamp in HFS+ format.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    return cls.FromPosixTime(hfs_time - cls.HFSTIME_TO_POSIX_BASE)

  @classmethod
  def FromJavaTime(cls, java_time):
    """Converts a Java time to a timestamp.

    Jave time is the number of milliseconds since
    January 1, 1970, 00:00:00 UTC.

    URL: http://docs.oracle.com/javase/7/docs/api/
         java/sql/Timestamp.html#getTime%28%29

    Args:
      java_time: The Java Timestamp.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    return java_time * cls.MILLI_SECONDS_TO_MICRO_SECONDS

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
      An integer containing the timestamp or 0 on error.
    """
    timestamp = cls.FromPosixTime(posix_time)
    if not timestamp:
      return 0
    return timestamp + microsecond

  @classmethod
  def FromPythonDatetime(cls, datetime_object):
    """Converts a Python datetime object into a timestamp."""
    if not isinstance(datetime_object, datetime.datetime):
      return 0

    posix_epoch = int(calendar.timegm(datetime_object.utctimetuple()))
    epoch = cls.FromPosixTime(posix_epoch)
    return epoch + datetime_object.microsecond

  @classmethod
  def FromTimeParts(
      cls, year, month, day, hour, minutes, seconds, microseconds=0,
      timezone=pytz.utc):
    """Converts a list of time entries to a timestamp.

    Args:
      year: An integer representing the year.
      month: An integer between 1 and 12.
      day: An integer representing the number of day in the month.
      hour: An integer representing the hour, 0 <= hour < 24.
      minutes: An integer, 0 <= minute < 60.
      seconds: An integer, 0 <= second < 60.
      microseconds: Optional number of microseconds ranging from:
                    0 <= microsecond < 1000000. The default is 0.
      timezone: Optional timezone (instance of pytz.timezone).
                The default is UTC.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    try:
      date = datetime.datetime(
          year, month, day, hour, minutes, seconds, microseconds)
    except ValueError as exception:
      logging.warning((
          u'Unable to create timestamp from {0:04d}-{1:02d}-{2:02d} '
          u'{3:02d}:{4:02d}:{5:02d}.{6:06d} with error: {7:s}').format(
              year, month, day, hour, minutes, seconds, microseconds,
              exception))
      return 0

    if type(timezone) is str:
      timezone = pytz.timezone(timezone)

    date_use = timezone.localize(date)
    epoch = int(calendar.timegm(date_use.utctimetuple()))

    return cls.FromPosixTime(epoch) + microseconds

  @classmethod
  def FromTimeString(
      cls, time_string, timezone=pytz.utc, dayfirst=False,
      gmt_as_timezone=True):
    """Converts a string containing a date and time value into a timestamp.

    Args:
      time_string: String that contains a date and time value.
      timezone: Optional timezone object (instance of pytz.timezone) that
                the data and time value in the string represents. This value
                is used when the timezone cannot be determined from the string.
      dayfirst: An optional boolean argument. If set to true then the
                parser will change the precedence in which it parses timestamps
                from MM-DD-YYYY to DD-MM-YYYY (and YYYY-MM-DD will be
                YYYY-DD-MM, etc).
      gmt_as_timezone: Sometimes the dateutil parser will interpret GMT and UTC
                       the same way, that is not make a distinction. By default
                       this is set to true, that is GMT can be intepreted
                       differently than UTC. If that is not the expected result
                       this attribute can be set to false.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    datetime_object = StringToDatetime(
        time_string, timezone=timezone, dayfirst=dayfirst,
        gmt_as_timezone=gmt_as_timezone)
    return cls.FromPythonDatetime(datetime_object)

  @classmethod
  def FromWebKitTime(cls, webkit_time):
    """Converts a WebKit time into a timestamp.

    The WebKit time is a 64-bit value containing:
      micro seconds since 1601-01-01 00:00:00

    Args:
      webkit_time: The 64-bit WebKit time timestamp.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    if webkit_time < (cls.TIMESTAMP_MIN_MICRO_SECONDS +
                      cls.WEBKIT_TIME_TO_POSIX_BASE):
      return 0
    return webkit_time - cls.WEBKIT_TIME_TO_POSIX_BASE

  @classmethod
  def GetNow(cls):
    """Retrieves the current time (now) as a timestamp in UTC."""
    time_elements = time.gmtime()
    return calendar.timegm(time_elements) * 1000000

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
  def LocaltimeToUTC(cls, timestamp, timezone, is_dst=False):
    """Converts the timestamp in localtime of the timezone to UTC.

    Args:
      timestamp: An integer containing the timestamp.
      timezone: The timezone (pytz.timezone) object.
      is_dst: A boolean to indicate the timestamp is corrected for daylight
              savings time (DST) only used for the DST transition period.
              The default is false.

    Returns:
      An integer containing the timestamp or 0 on error.
    """
    if timezone and timezone != pytz.utc:
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


def StringToDatetime(
    time_string, timezone=pytz.utc, dayfirst=False, gmt_as_timezone=True):
  """Converts a string representation of a timestamp into a datetime object.

  Args:
    time_string: String that contains a date and time value.
    timezone: Optional timezone object (instance of pytz.timezone) that
               the data and time value in the string represents. This value
               is used when the timezone cannot be determined from the string.
    dayfirst: An optional boolean argument. If set to true then the
              parser will change the precedence in which it parses timestamps
              from MM-DD-YYYY to DD-MM-YYYY (and YYYY-MM-DD will be YYYY-DD-MM,
              etc).
    gmt_as_timezone: Sometimes the dateutil parser will interpret GMT and UTC
                     the same way, that is not make a distinction. By default
                     this is set to true, that is GMT can be intepreted
                     differently than UTC. If that is not the expected result
                     this attribute can be set to false.

  Returns:
    A datetime object.
  """
  if not gmt_as_timezone and time_string.endswith(' GMT'):
    time_string = u'{0:s}UTC'.format(time_string[:-3])

  try:
    datetime_object = dateutil.parser.parse(time_string, dayfirst=dayfirst)

  except (TypeError, ValueError) as exception:
    logging.error(
        u'Unable to copy {0:s} to a datetime object with error: {1:s}'.format(
            time_string, exception))
    return datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=pytz.utc)

  if datetime_object.tzinfo:
    return datetime_object.astimezone(pytz.utc)

  return timezone.localize(datetime_object)


def GetCurrentYear():
  """Determines the current year."""
  datetime_object = datetime.datetime.now()
  return datetime_object.year
