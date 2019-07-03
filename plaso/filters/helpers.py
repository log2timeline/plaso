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
