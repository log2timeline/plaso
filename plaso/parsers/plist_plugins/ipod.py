# -*- coding: utf-8 -*-
"""This file contains a plist plugin for the iPod/iPhone storage plist."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


# TODO: add more attributes.
class IPodPlistEventData(events.EventData):
  """iPod plist event data.

  Attributes:
    device_id (str): unique identifier of the iPod device.
  """

  DATA_TYPE = 'ipod:device:entry'

  def __init__(self):
    """Initializes event data."""
    super(IPodPlistEventData, self).__init__(data_type=self.DATA_TYPE)
    self.device_id = None


class IPodPlugin(interface.PlistPlugin):
  """Plugin to extract iPod/iPad/iPhone device information."""

  NAME = 'ipod_device'
  DESCRIPTION = 'Parser for iPod, iPad and iPhone plist files.'

  PLIST_PATH = 'com.apple.iPod.plist'
  PLIST_KEYS = frozenset(['Devices'])

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extract device information from the iPod plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    devices = match.get('Devices', {})
    for device_identifier, device_information in iter(devices.items()):
      datetime_value = device_information.get('Connected', None)
      if not datetime_value:
        continue

      event_data = IPodPlistEventData()
      event_data.device_id = device_identifier

      # TODO: refactor.
      for key, value in iter(device_information.items()):
        if key == 'Connected':
          continue
        attribute_name = key.lower().replace(' ', '_')
        setattr(event_data, attribute_name, value)

      event = time_events.PythonDatetimeEvent(
          datetime_value, definitions.TIME_DESCRIPTION_LAST_CONNECTED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(IPodPlugin)
