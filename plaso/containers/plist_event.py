# -*- coding: utf-8 -*-
"""Plist event attribute containers."""

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib


class PlistEvent(time_events.TimestampEvent):
  """Plist event attribute container."""

  DATA_TYPE = u'plist:key'

  def __init__(self, root, key, datetime_time, desc=None, host=None, user=None):
    """Template for creating a Plist EventObject for returning data to Plaso.

    All events extracted from files get passed around Plaso internally as an
    EventObject. PlistEvent is an EventObject with attributes specifically
    relevant to data extracted from a Plist file. The attribute DATA_TYPE
    'plist:key' allows the formatter used during output to identify
    the appropriate formatter for converting these attributes to output.

    Args:
      root (str): path from the root to this key.
      key (str): name of key.
      datetime_time (datetime.datetime): datetime.
      desc (Optional[str]): description.
      host (Optional[str]): name of host.
      user (Optional[str]): name of user.
    """
    timestamp = timelib.Timestamp.FromPythonDatetime(datetime_time)
    super(PlistEvent, self).__init__(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
    self.desc = desc
    self.hostname = host
    self.key = key
    self.root = root
    self.username = user


# TODO: remove the need for this class.
class PlistTimeEventData(events.EventData):
  """Plist event data attribute container.

  Attributes:
    desc (str): description.
    host (str): hostname.
    key (str): name of plist key.
    root (str): path from the root to this plist key.
    user (str): unique username.
  """

  DATA_TYPE = u'plist:key'

  def __init__(self):
    """Initializes event data."""
    super(PlistTimeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.desc = None
    self.hostname = None
    self.key = None
    self.root = None
    self.username = None
