# -*- coding: utf-8 -*-
"""Plist parser plugin for Bluetooth plist files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class BluetoothPlugin(interface.PlistPlugin):
  """Plist parser plugin for Bluetooth plist files.

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
  DATA_FORMAT = 'Bluetooth plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.bluetooth.plist')])

  PLIST_KEYS = frozenset(['DeviceCache', 'PairedDevices'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant BT entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    device_cache = match.get('DeviceCache', {})
    for device, value in device_cache.items():
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

        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

        if device in match.get('PairedDevices', []):
          event_data.desc = 'Paired:True {0:s}'.format(name)
          event_data.key = device

          date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
          date_time.CopyFromDatetime(datetime_value)

          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = value.get('LastNameUpdate', None)
      if datetime_value:
        event_data.desc = ' '.join(filter(None, ('Device Name Set', name)))
        event_data.key = '{0:s}/LastNameUpdate'.format(device)

        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = value.get('LastServicesUpdate', None)
      if datetime_value:
        event_data.desc = ' '.join(filter(None, ('Services Updated', name)))
        event_data.key = '{0:s}/LastServicesUpdate'.format(device)

        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(BluetoothPlugin)
