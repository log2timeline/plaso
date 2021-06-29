# -*- coding: utf-8 -*-
"""Storage time range objects."""


class TimeRange(object):
  """Date and time range.

  The timestamp are integers containing the number of microseconds
  since January 1, 1970, 00:00:00 UTC.

  Attributes:
    duration (int): duration of the range in microseconds.
    end_timestamp (int): timestamp that marks the end of the range.
    start_timestamp (int): timestamp that marks the start of the range.
  """

  def __init__(self, start_timestamp, end_timestamp):
    """Initializes a date and time range.

    The timestamp are integers containing the number of microseconds
    since January 1, 1970, 00:00:00 UTC.

    Args:
      start_timestamp (int): timestamp that marks the start of the range.
      end_timestamp (int): timestamp that marks the end of the range.

    Raises:
      ValueError: If the time range is badly formed.
    """
    if start_timestamp is None or end_timestamp is None:
      raise ValueError(
          'Time range must have either a start and an end timestamp.')

    if start_timestamp > end_timestamp:
      raise ValueError(
          'Invalid start must be earlier than end timestamp.')

    super(TimeRange, self).__init__()
    self.duration = end_timestamp - start_timestamp
    self.end_timestamp = end_timestamp
    self.start_timestamp = start_timestamp
