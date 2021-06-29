# -*- coding: utf-8 -*-
"""Time-based event attribute containers."""

import datetime
import pytz

from plaso.containers import events
from plaso.lib import definitions


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
    if date_time.is_local_time and time_zone and time_zone != pytz.UTC:
      datetime_object = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=None)
      datetime_object += datetime.timedelta(microseconds=timestamp)

      datetime_delta = time_zone.utcoffset(datetime_object, is_dst=False)
      seconds_delta = int(datetime_delta.total_seconds())
      timestamp -= seconds_delta * definitions.MICROSECONDS_PER_SECOND

    super(DateTimeValuesEvent, self).__init__()
    self.date_time = date_time
    self.timestamp = timestamp
    self.timestamp_desc = date_time_description
