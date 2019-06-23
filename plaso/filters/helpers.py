# -*- coding: utf-8 -*-
"""The event filter expression parser helper functions and classes."""

from __future__ import unicode_literals

import codecs

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.lib import py2to3


def CopyValueToDateTime(value):
  """Copies an event filter value to a date and time object.

  Args:
    value (str): event filter value.

  Returns:
    dfdatetime.PosixTimeInMicroseconds: date and time object.

  Raises:
    ValueError: if the value cannot be copied to a date and time object.
  """
  if not isinstance(value, py2to3.INTEGER_TYPES):
    try:
      value = int(value, 10)
    except (TypeError, ValueError):
      pass

  if isinstance(value, py2to3.INTEGER_TYPES):
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=value)
  else:
    try:
      # Adjust the ISO 8601 string so is rembles a Python date and time string.
      if value and len(value) > 10 and value[10] == 'T':
        value = ' '.join(value.split('T'))

      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds()
      date_time.CopyFromDateTimeString(value)
    except (TypeError, ValueError):
      raise ValueError('Unsupported timestamp value: {0!s}'.format(value))

  return date_time


def GetUnicodeString(value):
  """Attempts to convert the argument to a Unicode string.

  Args:
    value (list|int|bytes|str): value to convert.

  Returns:
    str: string representation of the argument.
  """
  if isinstance(value, list):
    value = [GetUnicodeString(item) for item in value]
    return ''.join(value)

  if isinstance(value, py2to3.INTEGER_TYPES):
    value = '{0:d}'.format(value)

  if not isinstance(value, py2to3.UNICODE_TYPE):
    return codecs.decode(value, 'utf8', 'ignore')
  return value


class TimeRangeCache(object):
  """A class that stores time ranges from filters."""

  _INT64_MIN = -(1 << 63)
  _INT64_MAX = (1 << 63) - 1

  @classmethod
  def GetTimeRange(cls):
    """Retrives the first and last timestamp of filter range.

    Returns:
      tuple[int, int]: first and last timestamp of filter range.
    """
    first = getattr(cls, '_lower', cls._INT64_MIN)
    last = getattr(cls, '_upper', cls._INT64_MAX)

    if first < last:
      return first, last

    return last, first

  @classmethod
  def SetLowerTimestamp(cls, timestamp):
    """Sets the lower bound timestamp.

    Args:
      timestamp (int): first timestamp of filter range.
    """
    if not hasattr(cls, '_lower'):
      cls._lower = timestamp
      return

    if timestamp < cls._lower:
      cls._lower = timestamp

  @classmethod
  def SetUpperTimestamp(cls, timestamp):
    """Sets the upper bound timestamp.

    Args:
      timestamp (int): last timestamp of filter range.
    """
    if not hasattr(cls, '_upper'):
      cls._upper = timestamp
      return

    if timestamp > cls._upper:
      cls._upper = timestamp
