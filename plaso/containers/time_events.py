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


class CocoaTimeEvent(TimestampEvent):
  """Convenience class for a Cocoa time-based event."""

  def __init__(self, cocoa_time, timestamp_description, data_type=None):
    """Initializes an event.

    Args:
      cocoa_time (int): Cocoa time value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
    """
    timestamp = timelib.Timestamp.FromCocoaTime(cocoa_time)
    super(CocoaTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class DelphiTimeEvent(TimestampEvent):
  """Convenience class for a Delphi time-based event."""

  def __init__(self, delphi_time, timestamp_description, data_type=None):
    """Initializes an event.

    Args:
      delphi_time (int): Delphi time value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
    """
    timestamp = timelib.Timestamp.FromDelphiTime(delphi_time)
    super(DelphiTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class FatDateTimeEvent(TimestampEvent):
  """Convenience class for a FAT date time-based event."""

  def __init__(self, fat_date_time, timestamp_description, data_type=None):
    """Initializes an event.

    Args:
      fat_date_time (int): FAT date time value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
    """
    timestamp = timelib.Timestamp.FromFatDateTime(fat_date_time)
    super(FatDateTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class FiletimeEvent(TimestampEvent):
  """Convenience class for a FILETIME timestamp-based event."""

  def __init__(self, filetime, timestamp_description, data_type=None):
    """Initializes an event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
    """
    timestamp = timelib.Timestamp.FromFiletime(filetime)
    super(FiletimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class JavaTimeEvent(TimestampEvent):
  """Convenience class for a Java time-based event."""

  def __init__(self, java_time, timestamp_description, data_type=None):
    """Initializes an event.

    Args:
      java_time (int): Java timestamp, which contains the number of
          milliseconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
    """
    timestamp = timelib.Timestamp.FromJavaTime(java_time)
    super(JavaTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class PosixTimeEvent(TimestampEvent):
  """Convenience class for a POSIX time-based event."""

  def __init__(
      self, posix_time, timestamp_description, data_type=None, micro_seconds=0):
    """Initializes an event.

    Args:
      posix_time (int): POSIX time value, which contains the number of seconds
          since January 1, 1970 00:00:00 UTC.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
      micro_seconds: optional number of micro seconds.
    """
    if micro_seconds:
      timestamp = timelib.Timestamp.FromPosixTimeWithMicrosecond(
          posix_time, micro_seconds)
    else:
      timestamp = timelib.Timestamp.FromPosixTime(posix_time)

    super(PosixTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


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


class SystemtimeEvent(TimestampEvent):
  """Convenience class for a SYSTEMTIME timestamp-based event."""

  def __init__(self, systemtime, timestamp_description, data_type=None):
    """Initializes an event.

    Args:
      systemtime (bytes): 128-bit SYSTEMTIME timestamp value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
    """
    timestamp = timelib.Timestamp.FromSystemtime(systemtime)
    super(SystemtimeEvent, self).__init__(
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


class WebKitTimeEvent(TimestampEvent):
  """Convenience class for a WebKit time-based event."""

  def __init__(self, webkit_time, timestamp_description, data_type=None):
    """Initializes an event.

    Args:
      webkit_time (int): WebKit time value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      data_type (Optional[str]): event data type. If the data type is not set
          it is derived from the DATA_TYPE class attribute.
    """
    timestamp = timelib.Timestamp.FromWebKitTime(webkit_time)
    super(WebKitTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)
