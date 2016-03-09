# -*- coding: utf-8 -*-
"""This file is the template for Plist events."""

from plaso.containers import time_events
from plaso.lib import eventdata


class PlistEvent(time_events.PythonDatetimeEvent):
  """Convenience class for a plist events."""

  DATA_TYPE = 'plist:key'

  def __init__(self, root, key, timestamp, desc=None, host=None, user=None):
    """Template for creating a Plist EventObject for returning data to Plaso.

    All events extracted from files get passed around Plaso internally as an
    EventObject. PlistEvent is an EventObject with attributes specifically
    relevant to data extracted from a Plist file. The attribute DATA_TYPE
    'plist:key' allows the formatter used during output to identify
    the appropriate formatter for converting these attributes to output.

    Args:
      root: A string representing the path from the root to this key.
      key: A string representing the name of key.
      timestamp: The date object (instance of datetime.datetime).
      desc: An optional string intended for the user describing the event.
      host: An optional host name if one is available within the log file.
      user: An optional user name if one is available within the log file.
    """
    super(PlistEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME)

    self.root = root
    self.key = key
    if desc:
      self.desc = desc
    if host:
      self.hostname = host
    if user:
      self.username = user


class PlistTimeEvent(time_events.TimestampEvent):
  """Convenience class for a plist event that does not use datetime objects."""

  DATA_TYPE = 'plist:key'

  def __init__(self, root, key, timestamp, desc=None, host=None, user=None):
    """Template for creating a Plist EventObject for returning data to Plaso.

    All events extracted from files get passed around Plaso internally as an
    EventObject. PlistEvent is an EventObject with attributes specifically
    relevant to data extracted from a Plist file. The attribute DATA_TYPE
    'plist:key' allows the formatter used during output to identify
    the appropriate formatter for converting these attributes to output.

    Args:
      root: A string representing the path from the root to this key.
      key: A string representing the name of key.
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      desc: An optional string intended for the user describing the event.
      host: An optional host name if one is available within the log file.
      user: An optional user name if one is available within the log file.
    """
    super(PlistTimeEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME)

    self.root = root
    self.key = key
    if desc:
      self.desc = desc
    if host:
      self.hostname = host
    if user:
      self.username = user
