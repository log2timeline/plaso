# -*- coding: utf-8 -*-
"""Plist parser plugin for iPod, iPad and iPhone storage plist files."""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IPodPlistEventData(events.EventData):
  """iPod plist event data.

  Attributes:
    device_class (str): device class.
    device_identifier (str): identifier of the device.
    family_identifier (str): identifier of the device family.
    firmware_version (str): firmware version.
    imei (str): IMEI (International Mobile Equipment Identity).
    last_connected_time (dfdatetime.DateTimeValues): last date and time
        the iPod, iPad or iPhone storage (device) was connected.
    serial_number (str): serial number.
    use_count (str): number of times the device was used.
  """

  DATA_TYPE = 'ipod:device:entry'

  def __init__(self):
    """Initializes event data."""
    super(IPodPlistEventData, self).__init__(data_type=self.DATA_TYPE)
    self.device_class = None
    self.device_identifier = None
    self.family_identifier = None
    self.firmware_version = None
    self.imei = None
    self.last_connected_time = None
    self.serial_number = None
    self.use_count = None


class IPodPlugin(interface.PlistPlugin):
  """Plist parser plugin for iPod, iPad and iPhone storage plist files."""

  NAME = 'ipod_device'
  DATA_FORMAT = 'iPod, iPad and iPhone plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.iPod.plist')])

  PLIST_KEYS = frozenset(['Devices'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extract device information from the iPod plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    devices = match.get('Devices', {})
    for device_identifier, plist_key in devices.items():
      event_data = IPodPlistEventData()
      event_data.device_identifier = device_identifier
      event_data.device_class = plist_key.get('Device Class', None)
      event_data.family_identifier = plist_key.get('Family ID', None)
      event_data.firmware_version = plist_key.get(
          'Firmware Version String', None)
      event_data.imei = plist_key.get('IMEI', None)
      event_data.last_connected_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'Connected')
      event_data.serial_number = plist_key.get('Serial Number', None)
      event_data.use_count = plist_key.get('Use Count', None)

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(IPodPlugin)
