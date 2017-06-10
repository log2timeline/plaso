# -*- coding: utf-8 -*-
"""Bluetooth plist plugin."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
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

  NAME = u'macosx_bluetooth'
  DESCRIPTION = u'Parser for Bluetooth plist files.'

  PLIST_PATH = u'com.apple.bluetooth.plist'
  PLIST_KEYS = frozenset([u'DeviceCache', u'PairedDevices'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant BT entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    device_cache = match.get(u'DeviceCache', {})
    for device, value in iter(device_cache.items()):
      name = value.get(u'Name', u'')
      if name:
        name = u''.join((u'Name:', name))

      event_data = plist_event.PlistTimeEventData()
      event_data.root = u'/DeviceCache'

      datetime_value = value.get(u'LastInquiryUpdate', None)
      if datetime_value:
        event_data.desc = u' '.join(
            filter(None, (u'Bluetooth Discovery', name)))
        event_data.key = u'{0:s}/LastInquiryUpdate'.format(device)

        timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

        if device in match.get(u'PairedDevices', []):
          event_data.desc = u'Paired:True {0:s}'.format(name)
          event_data.key = device

          timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
          date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
              timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = value.get(u'LastNameUpdate', None)
      if datetime_value:
        event_data.desc = u' '.join(filter(None, (u'Device Name Set', name)))
        event_data.key = u'{0:s}/LastNameUpdate'.format(device)

        timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = value.get(u'LastServicesUpdate', None)
      if datetime_value:
        event_data.desc = u' '.join(filter(None, (u'Services Updated', name)))
        event_data.key = u'{0:s}/LastServicesUpdate'.format(device)

        timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

plist.PlistParser.RegisterPlugin(BluetoothPlugin)
