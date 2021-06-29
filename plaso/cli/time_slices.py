# -*- coding: utf-8 -*-
"""The time slice."""


class TimeSlice(object):
  """Time slice.

  The time slice is used to provide a context of events around an event
  of interest.

  Attributes:
    duration (int): duration of the time slice in minutes.
    event_timestamp (int): event timestamp of the time slice or None.
  """

  _MICRO_SECONDS_PER_MINUTE = 60 * 1000000

  def __init__(self, event_timestamp, duration=5):
    """Initializes the time slice.

    Args:
      event_timestamp (int): event timestamp of the time slice or None.
      duration (Optional[int]): duration of the time slice in minutes.
          The default is 5, which represent 2.5 minutes before and 2.5 minutes
          after the event timestamp.
    """
    super(TimeSlice, self).__init__()
    self.duration = duration
    self.event_timestamp = event_timestamp

  @property
  def end_timestamp(self):
    """int: slice end timestamp or None."""
    if self.event_timestamp:
      return self.event_timestamp + (
          self.duration * self._MICRO_SECONDS_PER_MINUTE)

    return None

  @property
  def start_timestamp(self):
    """int: slice start timestamp or None."""
    if self.event_timestamp:
      return self.event_timestamp - (
          self.duration * self._MICRO_SECONDS_PER_MINUTE)

    return None
