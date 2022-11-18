# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS Bluetooth plist files.

Fields within the plist key: com.apple.bluetooth.plist

LastInquiryUpdate:
  Device connected via Bluetooth discovery. Updated when a device is detected
  in discovery mode. E.g. Bluetooth headphone power on. Pairing is not required
  for a device to be discovered and cached.

LastNameUpdate:
  When the human name was last set. Usually done only once during initial setup.

LastServicesUpdate:
  Time set when device was polled to determine what it is. Usually done at setup
  or manually requested via advanced menu.
"""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSBluetoothEventData(events.EventData):
  """MacOS Bluetooth event data.

  Attributes:
    device_identifier (str): identifier of the device.
    device_name (str): name of the device.
    inquiry_time (dfdatetime.DateTimeValues): date and time of the most
        recent inquiry (connection during discovery mode) of a Bluetooth device.
    is_paired (bool): True if the device has been paired.
    name_update_time (dfdatetime.DateTimeValues): date and time of the most
        recent update of the human name.
    services_update_time (dfdatetime.DateTimeValues): date and time of the most
        recent poll of a Bluetooth device.
  """

  DATA_TYPE = 'macos:bluetooth:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSBluetoothEventData, self).__init__(data_type=self.DATA_TYPE)
    self.device_identifier = None
    self.device_name = None
    self.inquiry_time = None
    self.is_paired = None
    self.name_update_time = None
    self.services_update_time = None


class MacOSBluetoothPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS Bluetooth plist files."""

  NAME = 'macos_bluetooth'
  DATA_FORMAT = 'MacOS Bluetooth plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.bluetooth.plist')])

  PLIST_KEYS = frozenset(['DeviceCache', 'PairedDevices'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant BT entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    paired_devices = match.get('PairedDevices', [])

    for device_identifier, plist_key in match.get('DeviceCache', {}).items():
      event_data = MacOSBluetoothEventData()
      event_data.device_identifier = device_identifier
      event_data.device_name = plist_key.get('Name', None)
      event_data.inquiry_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'LastInquiryUpdate')
      event_data.is_paired = device_identifier in paired_devices
      event_data.name_update_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'LastNameUpdate')
      event_data.services_update_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'LastServicesUpdate')

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSBluetoothPlistPlugin)
