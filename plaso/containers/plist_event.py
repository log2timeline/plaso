# -*- coding: utf-8 -*-
"""Plist event attribute containers."""

from __future__ import unicode_literals

from plaso.containers import events


# TODO: remove the need for this class.
class PlistTimeEventData(events.EventData):
  """Plist event data attribute container.

  Attributes:
    desc (str): description.
    hostname (str): hostname.
    key (str): name of plist key.
    root (str): path from the root to this plist key.
    username (str): unique username.
  """

  DATA_TYPE = 'plist:key'

  def __init__(self):
    """Initializes event data."""
    super(PlistTimeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.desc = None
    self.hostname = None
    self.key = None
    self.root = None
    self.username = None
