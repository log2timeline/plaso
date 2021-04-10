# -*- coding: utf-8 -*-
"""Time manipulation functions and variables.

This module contain common methods that can be used to convert timestamps
from various formats into number of microseconds since January 1, 1970,
00:00:00 UTC that is used internally to store timestamps.

It also contains various functions to represent timestamps in a more
human readable form.
"""

import datetime

import pytz

from plaso.lib import definitions

# pylint: disable=missing-type-doc,missing-return-type-doc


class Timestamp(object):
  """Class for converting timestamps to Plaso timestamps.

  The Plaso timestamp is a 64-bit signed timestamp value containing:
  microseconds since 1970-01-01 00:00:00.

  The timestamp is not necessarily in UTC.
  """
  # Timestamp that represents the timestamp representing not
  # a date and time value.
  # TODO: replace this with a real None implementation.
  NONE_TIMESTAMP = 0

  @classmethod
  def LocaltimeToUTC(cls, timestamp, timezone, is_dst=False):
    """Converts the timestamp in localtime of the timezone to UTC.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of microseconds since January 1, 1970, 00:00:00 UTC.
      timezone: The timezone (pytz.timezone) object.
      is_dst: A boolean to indicate the timestamp is corrected for daylight
              savings time (DST) only used for the DST transition period.

    Returns:
      The timestamp which is an integer containing the number of microseconds
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
      timestamp -= seconds_delta * definitions.MICROSECONDS_PER_SECOND

    return timestamp
