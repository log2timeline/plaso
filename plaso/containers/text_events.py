# -*- coding: utf-8 -*-
"""This file contains the text format specific event object classes."""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.lib import py2to3


class TextEvent(time_events.TimestampEvent):
  """Convenience class for a text format-based event."""

  DATA_TYPE = 'text:entry'

  def __init__(self, timestamp, offset, attributes):
    """Initializes a text event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      offset: The offset of the attributes.
      attributes: A dict that contains the events attributes.
    """
    super(TextEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME)

    self.offset = offset

    for name, value in iter(attributes.items()):
      # TODO: Revisit this constraints and see if we can implement
      # it using a more sane solution.
      if isinstance(value, py2to3.STRING_TYPES) and not value:
        continue
      setattr(self, name, value)
