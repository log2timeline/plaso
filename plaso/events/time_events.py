# -*- coding: utf-8 -*-
"""This file contains the time-based event object classes."""

from plaso.lib import event
from plaso.lib import timelib


class TimestampEvent(event.EventObject):
  """Convenience class for a timestamp-based event.

  Attributes:
    data_type: the event data type.
    timestamp: the timestamp which is an integer containing the number
               of micro seconds since January 1, 1970, 00:00:00 UTC.
    timestamp_desc: the description of the usage of the timestamp.
  """

  def __init__(self, timestamp, timestamp_description, data_type=None):
    """Initializes an event object.

    Args:
      timestamp: the timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: the usage string for the timestamp value.
      data_type: optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    super(TimestampEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = timestamp_description

    if data_type:
      self.data_type = data_type


class CocoaTimeEvent(TimestampEvent):
  """Convenience class for a Cocoa time-based event."""

  def __init__(self, cocoa_time, timestamp_description, data_type=None):
    """Initializes an event object.

    Args:
      cocoa_time: the Cocoa time value.
      timestamp_description: the usage string for the timestamp value.
      data_type: optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    timestamp = timelib.Timestamp.FromCocoaTime(cocoa_time)
    super(CocoaTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class DelphiTimeEvent(TimestampEvent):
  """Convenience class for a Delphi time-based event."""

  def __init__(self, delphi_time, timestamp_description, data_type=None):
    """Initializes an event object.

    Args:
      delphi_time: the Delphi time value.
      timestamp_description: the usage string for the timestamp value.
      data_type: optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    timestamp = timelib.Timestamp.FromDelphiTime(delphi_time)
    super(DelphiTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class FatDateTimeEvent(TimestampEvent):
  """Convenience class for a FAT date time-based event."""

  def __init__(self, fat_date_time, timestamp_description, data_type=None):
    """Initializes an event object.

    Args:
      fat_date_time: the FAT date time value.
      timestamp_description: the usage string for the timestamp value.
      data_type: optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    timestamp = timelib.Timestamp.FromFatDateTime(fat_date_time)
    super(FatDateTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class FiletimeEvent(TimestampEvent):
  """Convenience class for a FILETIME timestamp-based event."""

  def __init__(self, filetime, timestamp_description, data_type=None):
    """Initializes an event object.

    Args:
      filetime: the FILETIME timestamp value.
      timestamp_description: the usage string for the timestamp value.
      data_type: optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    timestamp = timelib.Timestamp.FromFiletime(filetime)
    super(FiletimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class JavaTimeEvent(TimestampEvent):
  """Convenience class for a Java time-based event."""

  def __init__(self, java_time, timestamp_description, data_type=None):
    """Initializes an event object.

    Args:
      java_time: the Java timestamp which is an integer containing the number
                 of milliseconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: the usage string for the timestamp value.
      data_type: optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    timestamp = timelib.Timestamp.FromJavaTime(java_time)
    super(JavaTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class PosixTimeEvent(TimestampEvent):
  """Convenience class for a POSIX time-based event."""

  def __init__(
      self, posix_time, timestamp_description, data_type=None, micro_seconds=0):
    """Initializes an event object.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      timestamp_description: the usage string for the timestamp value.
      data_type: optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
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
    """Initializes an event object.

    Args:
      datetime_time: the datetime object (instance of datetime.datetime).
      timestamp_description: the usage string for the timestamp value.
      data_type: optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    timestamp = timelib.Timestamp.FromPythonDatetime(datetime_time)
    super(PythonDatetimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)


class UUIDTimeEvent(TimestampEvent):
  """Convenience class for an UUID version time-based event.

  Attributes:
    mac_address: the MAC address stored in the UUID.
  """

  def __init__(self, uuid, timestamp_description):
    """Initializes an event object.

    Args:
      uuid: a uuid object (instance of uuid.UUID).
      timestamp_description: the usage string for the timestamp value.

    Raises:
      ValueError: if the UUID version is not supported.
    """
    if not uuid.version == 1:
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
    """Initializes an event object.

    Args:
      webkit_time: the WebKit time value.
      timestamp_description: the usage string for the timestamp value.
      data_type: optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    timestamp = timelib.Timestamp.FromWebKitTime(webkit_time)
    super(WebKitTimeEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)
