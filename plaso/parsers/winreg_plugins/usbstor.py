# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the USBStor key.

Also see:
  https://forensics.wiki/usb_history_viewing
"""

import os

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class USBStorDeviceInstanceEventData(events.EventData):
  """USBStor device instance event data attribute container.

  Attributes:
    device_last_arrival_time (dfdatetime.DateTimeValues): date and time of
        the device insertion.
    device_last_removal_time (dfdatetime.DateTimeValues): date and time of
        the removal insertion.
    device_type (str): type of USB device.
    display_name (str): display name of the USB device.
    key_path (str): Windows Registry key path.
    driver_first_installation_time (dfdatetime.DateTimeValues): date and time of
        when the device instance was first installed in the system
    driver_last_installation_time (dfdatetime.DateTimeValues): date and time of
        when the current device instance was installed in the system.
    firmware_time (dfdatetime.DateTimeValues): date and time of
        the firmware.
    product (str): product of the USB device.
    revision (str): revision number of the USB device.
    vendor (str): vendor of the USB device.
  """

  DATA_TYPE = 'windows:registry:usbstor:instance'

  def __init__(self):
    """Initializes event data."""
    super(USBStorDeviceInstanceEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.device_last_arrival_time = None
    self.device_last_removal_time = None
    self.device_type = None
    self.display_name = None
    self.driver_first_installation_time = None
    self.driver_last_installation_time = None
    self.firmware_time = None
    self.key_path = None
    self.product = None
    self.revision = None
    self.vendor = None


class USBStorPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """USBStor key plugin."""

  NAME = 'windows_usbstor_devices'
  DATA_FORMAT = 'Windows USB Plug And Play Manager USBStor Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum\\USBSTOR')])

  _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), 'usbstor.yaml')

  def _GetPropertyValueData(self, property_value_key, value_type):
    """Retrieves a property value data.

    Args:
      property_value_key (dfwinreg.WinRegistryKey): property value Windows
          Registry key.
      value_type (int): value type.

    Returns:
      object: property value data.

    Raises:
      ParseError: if the property value data cannot be determined.
    """
    binary_data = self._GetValueDataFromKey(property_value_key, 'Data')

    if value_type == 0x00000007:
      data_type_map = self._GetDataTypeMap('uint32le')
    elif value_type == 0x00000010:
      data_type_map = self._GetDataTypeMap('uint64le')
    elif value_type == 0x00000012:
      data_type_map = self._GetDataTypeMap('utf16le_string')
    else:
      raise errors.ParseError('Unsupported value type: 0x{0:08x}'.format(
          value_type))

    try:
      value_data = self._ReadStructureFromByteStream(
          binary_data, 0, data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse value: Data with error: {0!s}'.format(exception))

    if value_type == 0x00000010:
      value_data = dfdatetime_filetime.Filetime(timestamp=value_data)

    return value_data

  def _GetPropertyValueType(self, property_value_key):
    """Retrieves a property value type.

    Args:
      property_value_key (dfwinreg.WinRegistryKey): property value Windows
          Registry key.

    Returns:
      int: property value type.

    Raises:
      ParseError: if the property value type cannot be determined.
    """
    binary_data = self._GetValueDataFromKey(property_value_key, 'Type')

    data_type_map = self._GetDataTypeMap('uint32le')

    try:
      return self._ReadStructureFromByteStream(binary_data, 0, data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse value: Type with error: {0!s}'.format(exception))

  def _ParseDeviceKey(self, parser_mediator, device_key):
    """Parses an USB storage device key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      device_key (dfwinreg.WinRegistryKey): USB storage device Windows Registry
          key.

    Returns:
      USBStorageDevice: an USB storage device.
    """
    name_values = device_key.name.split('&')
    device_type = None
    product = None
    revision = None
    vendor = None

    number_of_name_values = len(name_values)
    if number_of_name_values >= 1:
      device_type = name_values[0]
    if number_of_name_values >= 2:
      vendor = name_values[1]
    if number_of_name_values >= 3:
      product = name_values[2]
    if number_of_name_values >= 4:
      revision = name_values[3]

    for device_instance_key in device_key.GetSubkeys():
      properties = {}

      properties_key = device_instance_key.GetSubkeyByName('Properties')
      if properties_key:
        for property_set_key in properties_key.GetSubkeys():
          for property_key in property_set_key.GetSubkeys():
            for property_value_key in property_key.GetSubkeys():
              lookup_key = ':'.join([
                  property_set_key.name, property_key.name]).lower()
              value_type = self._GetPropertyValueType(property_value_key)
              properties[lookup_key] = self._GetPropertyValueData(
                  property_value_key, value_type)

      event_data = USBStorDeviceInstanceEventData()
      event_data.device_last_arrival_time = properties.get(
          '{83da6326-97a6-4088-9453-a1923f573b29}:00000066', None)
      event_data.device_last_removal_time = properties.get(
          '{83da6326-97a6-4088-9453-a1923f573b29}:00000067', None)
      event_data.device_type = device_type
      event_data.display_name = self._GetValueFromKey(
          device_instance_key, 'FriendlyName')
      event_data.driver_first_installation_time = properties.get(
          '{83da6326-97a6-4088-9453-a1923f573b29}:00000064', None)
      event_data.driver_last_installation_time = properties.get(
          '{83da6326-97a6-4088-9453-a1923f573b29}:00000065', None)
      event_data.firmware_time = properties.get(
          '{540b947e-8b40-45bc-a8a2-6a0b894cbda2}:00000011', None)
      event_data.key_path = device_instance_key.path
      event_data.product = product
      event_data.revision = revision
      event_data.vendor = vendor

      parser_mediator.ProduceEventData(event_data)

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for device_key in registry_key.GetSubkeys():
      try:
        self._ParseDeviceKey(parser_mediator, device_key)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse device key with error: {0!s}'.format(exception))
        continue

    self._ProduceDefaultWindowsRegistryEvent(parser_mediator, registry_key)


winreg_parser.WinRegistryParser.RegisterPlugin(USBStorPlugin)
