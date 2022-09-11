# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS Bluetooth plist files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSBluetoothEventData(events.EventData):
  """MacOS Bluetooth event data.

  Attributes:
    device_identifier (str): identifier of the device.
    device_name (str): name of the device.
    is_paired (bool): True if the device has been paired.
  """

  DATA_TYPE = 'macos:bluetooth:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSBluetoothEventData, self).__init__(data_type=self.DATA_TYPE)
    self.device_identifier = None
    self.device_name = None
    self.is_paired = None


class MacOSBluetoothPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS Bluetooth plist files.

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

  # TODO: rename to macos_bluetooth
  NAME = 'macosx_bluetooth'
  DATA_FORMAT = 'MacOS Bluetooth plist file'

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
    paired_devices = match.get('PairedDevices', [])

    device_cache = match.get('DeviceCache', {})
    for device_identifier, value in device_cache.items():
      event_data = MacOSBluetoothEventData()
      event_data.device_identifier = device_identifier
      event_data.device_name = value.get('Name', None)
      event_data.is_paired = device_identifier in paired_devices

      datetime_value = value.get('LastInquiryUpdate', None)
      if datetime_value:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, 'Last Inquiry Update Time')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = value.get('LastNameUpdate', None)
      if datetime_value:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, 'Last Name Update Time')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = value.get('LastServicesUpdate', None)
      if datetime_value:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, 'Last Services Update Time')
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(MacOSBluetoothPlistPlugin)
