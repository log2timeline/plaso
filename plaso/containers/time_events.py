# -*- coding: utf-8 -*-
"""This file contains the time-based event classes."""

from plaso.containers import events
from plaso.lib import timelib


class TimestampEvent(events.EventObject):
  """Convenience class for a timestamp-based event.

  Attributes:
    data_type (str): event data type.
    timestamp (int): timestamp, which contains the number of microseconds
        since January 1, 1970, 00:00:00 UTC.
    timestamp_desc (str): description of the meaning of the timestamp.
  """

  def __init__(self, timestamp, timestamp_description, data_type=None):
    """Initializes an event.

    Args:
      timestamp (int): timestamp, which contains the number of microseconds
          since January 1, 1970, 00:00:00 UTC.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
    """
    super(TimestampEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = timestamp_description

    if data_type:
      self.data_type = data_type


class DateTimeValuesEvent(TimestampEvent):
  """Convenience class for a dfdatetime-based event."""

  def __init__(
      self, date_time, date_time_description, data_type=None, time_zone=None):
    """Initializes an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date and
          time values.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
      time_zone (Optional[datetime.tzinfo]): time zone.
    """
    timestamp = date_time.GetPlasoTimestamp()
    if date_time.is_local_time and time_zone:
      timestamp = timelib.Timestamp.LocaltimeToUTC(timestamp, time_zone)

    super(DateTimeValuesEvent, self).__init__(
        timestamp, date_time_description, data_type=data_type)


class PythonDatetimeEvent(TimestampEvent):
  """Convenience class for a Python DateTime time-based event."""

  def __init__(self, datetime_time, timestamp_description, data_type=None):
    """Initializes an event.

    Args:
      datetime_time (datetime.datetime): datetime.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
    """
    timestamp = timelib.Timestamp.FromPythonDatetime(datetime_time)
    super(PythonDatetimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class UUIDTimeEvent(TimestampEvent):
  """Convenience class for an UUID version time-based event.

  Attributes:
    mac_address (str): MAC address stored in the UUID.
  """

  def __init__(self, uuid, timestamp_description):
    """Initializes an event.

    Args:
      uuid (uuid.UUID): UUID.
      timestamp_description (str): description of the meaning of the timestamp
          value.

    Raises:
      ValueError: if the UUID version is not supported.
    """
    if uuid.version != 1:
      raise ValueError(u'Unsupported UUID version.')

    timestamp = timelib.Timestamp.FromUUIDTime(uuid.time)
    mac_address = u'{0:s}:{1:s}:{2:s}:{3:s}:{4:s}:{5:s}'.format(
        uuid.hex[20:22], uuid.hex[22:24], uuid.hex[24:26], uuid.hex[26:28],
        uuid.hex[28:30], uuid.hex[30:32])
    super(UUIDTimeEvent, self).__init__(timestamp, timestamp_description)

    self.mac_address = mac_address
    self.uuid = u'{0!s}'.format(uuid)
