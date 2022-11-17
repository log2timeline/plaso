# -*- coding: utf-8 -*-
"""Plist event attribute containers."""

from plaso.containers import events


# TODO: remove the need for this class.
class PlistTimeEventData(events.EventData):
  """Plist event data attribute container.

  Attributes:
    key (str): name of plist key.
    root (str): path from the root to this plist key.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'plist:key'

  def __init__(self):
    """Initializes event data."""
    super(PlistTimeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key = None
    self.root = None
    self.written_time = None
