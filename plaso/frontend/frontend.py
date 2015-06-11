# -*- coding: utf-8 -*-
"""The common front-end functionality."""


class Frontend(object):
  """Class that implements a front-end."""


class TimeSlice(object):
  """Class that defines a time slice.

  The time slice is used to provide a context of events around an event
  of interest.

  Attributes:
    duration: duration of the time slize in minutes.
    event_timestamp: event timestamp of the time slice or None.
  """

  _MICRO_SECONDS_PER_MINUTE = 60 * 1000000

  def __init__(self, event_timestamp, duration=5):
    """Initializes the time slice.

    Args:
      event_timestamp: event timestamp of the time slice or None.
      duration: optional duration of the time slize in minutes.
                The default is 5, which represent 2.5 minutes before
                and 2.5 minutes after the event timestamp.
    """
    super(TimeSlice, self).__init__()
    self.duration = duration
    self.event_timestamp = event_timestamp

  @property
  def end_timestamp(self):
    """The slice end timestamp or None."""
    if not self.event_timestamp:
      return
    return self.event_timestamp + (
        self.duration * self._MICRO_SECONDS_PER_MINUTE)

  @property
  def start_timestamp(self):
    """The slice start timestamp or None."""
    if not self.event_timestamp:
      return
    return self.event_timestamp - (
        self.duration * self._MICRO_SECONDS_PER_MINUTE)
