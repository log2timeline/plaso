# -*- coding: utf-8 -*-
"""Storage time range objects."""

class TimeRange(object):
  """A class that defines a date and time range.

  The timestamp are integers containing the number of micro seconds
  since January 1, 1970, 00:00:00 UTC.

  Attributes:
    start_timestamp: integer containing the timestamp that marks
                     the start of the range.
    end_timestamp: integer containing the timestamp that marks
                   the end of the range.
  """

  def __init__(self, start_timestamp, end_timestamp):
    """Initializes a date and time range object.

    The timestamp are integers containing the number of micro seconds
    since January 1, 1970, 00:00:00 UTC.

    Args:
      start_timestamp: integer containing the timestamp that marks
                       the start of the range.
      end_timestamp: integer containing the timestamp that marks
                     the end of the range.

    Raises:
      ValueError: If the time range is badly formed.
    """
    if start_timestamp is None or end_timestamp is None:
      raise ValueError(
          u'Time range must have either a start and an end timestamp.')

    if start_timestamp > end_timestamp:
      raise ValueError(
          u'Invalid start must be earlier than end timestamp.')

    super(TimeRange, self).__init__()
    self.end_timestamp = end_timestamp
    self.start_timestamp = start_timestamp
