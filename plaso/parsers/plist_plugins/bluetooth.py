# -*- coding: utf-8 -*-
"""Bluetooth plist plugin."""

from __future__ import unicode_literals

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class BluetoothPlugin(interface.PlistPlugin):
  """Basic plugin to extract interesting Bluetooth related keys.

  Additional details about the fields.

  LastInquiryUpdate:
    Device connected via Bluetooth Discovery. Updated
    when a device is detected in discovery mode. E.g. BT headphone power
    on. Pairing is not required for a device to be discovered and cached.

  LastNameUpdate:
    When the human name was last set. Usually done only once during
    initial setup.

  LastServicesUpdate:
    Time set when device was polled to determine what it is. Usually
    done at setup or manually requested via advanced menu.
  """

  NAME = 'macosx_bluetooth'
  DESCRIPTION = 'Parser for Bluetooth plist files.'

  PLIST_PATH = 'com.apple.bluetooth.plist'
  PLIST_KEYS = frozenset(['DeviceCache', 'PairedDevices'])

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant BT entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    device_cache = match.get('DeviceCache', {})
    for device, value in iter(device_cache.items()):
      name = value.get('Name', '')
      if name:
        name = ''.join(('Name:', name))

      event_data = plist_event.PlistTimeEventData()
      event_data.root = '/DeviceCache'

      datetime_value = value.get('LastInquiryUpdate', None)
      if datetime_value:
        event_data.desc = ' '.join(
            filter(None, ('Bluetooth Discovery', name)))
        event_data.key = '{0:s}/LastInquiryUpdate'.format(device)

        event = time_events.PythonDatetimeEvent(
            datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

        if device in match.get('PairedDevices', []):
          event_data.desc = 'Paired:True {0:s}'.format(name)
          event_data.key = device

          event = time_events.PythonDatetimeEvent(
              datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = value.get('LastNameUpdate', None)
      if datetime_value:
        event_data.desc = ' '.join(filter(None, ('Device Name Set', name)))
        event_data.key = '{0:s}/LastNameUpdate'.format(device)

        event = time_events.PythonDatetimeEvent(
            datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = value.get('LastServicesUpdate', None)
      if datetime_value:
        event_data.desc = ' '.join(filter(None, ('Services Updated', name)))
        event_data.key = '{0:s}/LastServicesUpdate'.format(device)

        event = time_events.PythonDatetimeEvent(
            datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(BluetoothPlugin)
