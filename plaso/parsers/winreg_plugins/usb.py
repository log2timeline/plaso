# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the USB Device key.

Also see:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/
"""

from plaso.containers import events
from plaso.parsers import logger
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WindowsUSBDeviceEventData(events.EventData):
  """Windows USB device event data attribute container.

  Attributes:
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    product (str): product of the USB device.
    serial (str): serial number of the USB device.
    subkey_name (str): name of the Windows Registry subkey.
    vendor (str): vendor of the USB device.
  """

  DATA_TYPE = 'windows:registry:usb'

  def __init__(self):
    """Initializes event data."""
    super(WindowsUSBDeviceEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None
    self.last_written_time = None
    self.product = None
    self.serial = None
    # TODO: rename subkey_name to something that closer matches its purpose.
    self.subkey_name = None
    self.vendor = None


class USBPlugin(interface.WindowsRegistryPlugin):
  """USB Windows Registry plugin for last connection time."""

  NAME = 'windows_usb_devices'
  DATA_FORMAT = 'Windows USB device Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum\\USB')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    event_data = WindowsUSBDeviceEventData()
    event_data.key_path = registry_key.path

    for subkey in registry_key.GetSubkeys():
      event_data.subkey_name = subkey.name

      vendor_identification = None
      product_identification = None

      try:
        subkey_name_parts = subkey.name.split('&')
        if len(subkey_name_parts) >= 2:
          vendor_identification = subkey_name_parts[0]
          product_identification = subkey_name_parts[1]
      except ValueError as exception:
        logger.warning('Unable to split string: {0:s} with error: {1!s}'.format(
            subkey.name, exception))

      event_data.vendor = vendor_identification
      event_data.product = product_identification

      for devicekey in subkey.GetSubkeys():
        # The last written time of the Registry key relates to the last time
        # an USB device was connected to the operating system.
        event_data.last_written_time = devicekey.last_written_time
        event_data.serial = devicekey.name

        parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(USBPlugin)
