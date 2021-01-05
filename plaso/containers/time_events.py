# -*- coding: utf-8 -*-
"""Time-based event attribute containers."""

from plaso.containers import events
from plaso.lib import timelib


class DateTimeValuesEvent(events.EventObject):
  """dfDateTime date time values-based event attribute container.

  Attributes:
    date_time (dfdatetime.DateTimeValues): date and time values.
    timestamp (int): timestamp, which contains the number of microseconds
        since January 1, 1970, 00:00:00 UTC.
    timestamp_desc (str): description of the meaning of the timestamp.
  """

  def __init__(self, date_time, date_time_description, time_zone=None):
    """Initializes an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date and
          time values.
      time_zone (Optional[datetime.tzinfo]): time zone.
    """
    timestamp = date_time.GetPlasoTimestamp()
    if date_time.is_local_time and time_zone:
      timestamp = timelib.Timestamp.LocaltimeToUTC(timestamp, time_zone)

    super(DateTimeValuesEvent, self).__init__()
    self.date_time = date_time
    self.timestamp = timestamp
    self.timestamp_desc = date_time_description
