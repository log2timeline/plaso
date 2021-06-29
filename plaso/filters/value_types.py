# -*- coding: utf-8 -*-
"""Value types that can be used in an event filter."""

from dfdatetime import posix_time as dfdatetime_posix_time


class DateTimeValueType(dfdatetime_posix_time.PosixTimeInMicroseconds):
  """Value type to represent a date and time value."""

  def __init__(self, value):
    """Initializes a date and time value type.

    Args:
      value (int:str): a POSIX timestamp in microseconds or an ISO 8601 date
          and time string.

    Raises:
      ValueError: if the value cannot be copied to a date and time object.
    """
    if isinstance(value, int):
      timestamp = value
    else:
      try:
        timestamp = int(value, 10)
      except (TypeError, ValueError):
        timestamp = None

    super(DateTimeValueType, self).__init__(timestamp=timestamp)

    if timestamp is None:
      try:
        # Adjust the ISO 8601 date and time string so is resembles a Python
        # date and time string.
        if value and len(value) > 10 and value[10] == 'T':
          value = ' '.join(value.split('T'))

        self.CopyFromDateTimeString(value)
      except (TypeError, ValueError):
        raise ValueError('Unsupported date time string value: {0!s}'.format(
            value))
