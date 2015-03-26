# -*- coding: utf-8 -*-
"""This file contains the time-based event object classes."""

from plaso.lib import event
from plaso.lib import timelib


class TimestampEvent(event.EventObject):
  """Convenience class for a timestamp-based event."""

  def __init__(self, timestamp, usage, data_type=None):
    """Initializes an event object.

    Args:
      timestamp: The timestamp value.
      usage: The description of the usage of the time value.
      data_type: Optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    super(TimestampEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = usage

    if data_type:
      self.data_type = data_type


class CocoaTimeEvent(TimestampEvent):
  """Convenience class for a Cocoa time-based event."""

  def __init__(self, cocoa_time, usage, data_type=None):
    """Initializes an event object.

    Args:
      cocoa_time: The Cocoa time value.
      usage: The description of the usage of the time value.
      data_type: Optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    super(CocoaTimeEvent, self).__init__(
        timelib.Timestamp.FromCocoaTime(cocoa_time), usage,
        data_type=data_type)


class FatDateTimeEvent(TimestampEvent):
  """Convenience class for a FAT date time-based event."""

  def __init__(self, fat_date_time, usage, data_type=None):
    """Initializes an event object.

    Args:
      fat_date_time: The FAT date time value.
      usage: The description of the usage of the time value.
      data_type: Optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    super(FatDateTimeEvent, self).__init__(
        timelib.Timestamp.FromFatDateTime(fat_date_time), usage,
        data_type=data_type)


class FiletimeEvent(TimestampEvent):
  """Convenience class for a FILETIME timestamp-based event."""

  def __init__(self, filetime, usage, data_type=None):
    """Initializes an event object.

    Args:
      filetime: The FILETIME timestamp value.
      usage: The description of the usage of the time value.
      data_type: Optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    super(FiletimeEvent, self).__init__(
        timelib.Timestamp.FromFiletime(filetime), usage, data_type=data_type)


class JavaTimeEvent(TimestampEvent):
  """Convenience class for a Java time-based event."""

  def __init__(self, java_time, usage, data_type=None):
    """Initializes an event object.

    Args:
      java_time: The Java time value.
      usage: The description of the usage of the time value.
      data_type: Optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    super(JavaTimeEvent, self).__init__(
        timelib.Timestamp.FromJavaTime(java_time), usage, data_type=data_type)


class PosixTimeEvent(TimestampEvent):
  """Convenience class for a POSIX time-based event."""

  def __init__(self, posix_time, usage, data_type=None):
    """Initializes an event object.

    Args:
      posix_time: The POSIX time value.
      usage: The description of the usage of the time value.
      data_type: Optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    super(PosixTimeEvent, self).__init__(
        timelib.Timestamp.FromPosixTime(posix_time), usage, data_type=data_type)


class PythonDatetimeEvent(TimestampEvent):
  """Convenience class for a Python DateTime time-based event."""

  def __init__(self, datetime_time, usage, data_type=None):
    """Initializes an event object.

    Args:
      datetime_time: The datetime object (instance of datetime.datetime).
      usage: The description of the usage of the time value.
      data_type: Optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    super(PythonDatetimeEvent, self).__init__(
        timelib.Timestamp.FromPythonDatetime(datetime_time), usage,
        data_type=data_type)


class WebKitTimeEvent(TimestampEvent):
  """Convenience class for a WebKit time-based event."""

  def __init__(self, webkit_time, usage, data_type=None):
    """Initializes an event object.

    Args:
      webkit_time: The WebKit time value.
      usage: The description of the usage of the time value.
      data_type: Optional event data type. If not set data_type is
                 derived from the DATA_TYPE attribute.
    """
    super(WebKitTimeEvent, self).__init__(
        timelib.Timestamp.FromWebKitTime(webkit_time), usage,
        data_type=data_type)
