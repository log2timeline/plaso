# -*- coding: utf-8 -*-
"""This file contains a plist plugin for the iPod/iPhone storage plist."""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IPodPlistEvent(time_events.PythonDatetimeEvent):
  """An event object for an entry in the iPod plist file."""

  DATA_TYPE = u'ipod:device:entry'

  def __init__(self, datetime_timestamp, device_id, device_info):
    """Initialize the event.

    Args:
      datetime_timestamp: The timestamp for the event as a datetime object.
      device_id: The device ID.
      device_info: A dict that contains extracted information from the plist.
    """
    super(IPodPlistEvent, self).__init__(
        datetime_timestamp, eventdata.EventTimestamp.LAST_CONNECTED)

    self.device_id = device_id

    # Save the other attributes.
    for key, value in device_info.iteritems():
      if key == u'Connected':
        continue
      attribute_name = key.lower().replace(u' ', u'_')
      setattr(self, attribute_name, value)


class IPodPlugin(interface.PlistPlugin):
  """Plugin to extract iPod/iPad/iPhone device information."""

  NAME = u'ipod_device'
  DESCRIPTION = u'Parser for iPod, iPad and iPhone plist files.'

  PLIST_PATH = u'com.apple.iPod.plist'
  PLIST_KEYS = frozenset([u'Devices'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extract device information from the iPod plist.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
    """
    if not u'Devices' in match:
      return

    devices = match[u'Devices']
    if not devices:
      return

    for device, device_info in devices.iteritems():
      if u'Connected' not in device_info:
        continue
      event_object = IPodPlistEvent(
          device_info.get(u'Connected'), device, device_info)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(IPodPlugin)
