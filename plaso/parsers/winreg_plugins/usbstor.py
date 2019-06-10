# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the USBStor key."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class USBStorEventData(events.EventData):
  """USBStor event data attribute container.

  Attributes:
    device_type (str): type of USB device.
    display_name (str): display name of the USB device.
    key_path (str): Windows Registry key path.
    parent_id_prefix (str): parent identifier prefix of the USB device.
    product (str): product of the USB device.
    serial (str): serial number of the USB device.
    revision (str): revision number of the USB device.
    subkey_name (str): name of the Windows Registry subkey.
    vendor (str): vendor of the USB device.
  """

  DATA_TYPE = 'windows:registry:usbstor'

  def __init__(self):
    """Initializes event data."""
    super(USBStorEventData, self).__init__(data_type=self.DATA_TYPE)
    self.device_type = None
    self.display_name = None
    self.key_path = None
    self.parent_id_prefix = None
    self.product = None
    self.revision = None
    self.serial = None
    # TODO: rename subkey_name to something that closer matches its purpose.
    self.subkey_name = None
    self.vendor = None


class USBStorPlugin(interface.WindowsRegistryPlugin):
  """USBStor key plugin.

  Also see:
    http://www.forensicswiki.org/wiki/USB_History_Viewing
  """

  NAME = 'windows_usbstor_devices'
  DESCRIPTION = 'Parser for USB Plug And Play Manager USBStor Registry Key.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum\\USBSTOR')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for subkey in registry_key.GetSubkeys():
      subkey_name = subkey.name

      name_values = subkey_name.split('&')
      number_of_name_values = len(name_values)

      # Normally we expect 4 fields here however that is not always the case.
      if number_of_name_values != 4:
        logger.warning(
            'Expected 4 &-separated values in: {0:s}'.format(subkey_name))

      event_data = USBStorEventData()
      event_data.key_path = registry_key.path
      event_data.subkey_name = subkey_name

      if number_of_name_values >= 1:
        event_data.device_type = name_values[0]
      if number_of_name_values >= 2:
        event_data.vendor = name_values[1]
      if number_of_name_values >= 3:
        event_data.product = name_values[2]
      if number_of_name_values >= 4:
        event_data.revision = name_values[3]

      if subkey.number_of_subkeys == 0:
        # Time last USB device of this class was first inserted.
        event = time_events.DateTimeValuesEvent(
            subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)
        continue

      for device_key in subkey.GetSubkeys():
        event_data.serial = device_key.name

        friendly_name_value = device_key.GetValueByName('FriendlyName')
        if friendly_name_value:
          event_data.display_name = friendly_name_value.GetDataAsObject()

        # ParentIdPrefix applies to Windows XP Only.
        parent_id_prefix_value = device_key.GetValueByName('ParentIdPrefix')
        if parent_id_prefix_value:
          event_data.parent_id_prefix = parent_id_prefix_value.GetDataAsObject()

        # Time last USB device of this class was first inserted.
        event = time_events.DateTimeValuesEvent(
            subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

        # Win7 - Last Connection.
        # Vista/XP - Time of an insert.
        event = time_events.DateTimeValuesEvent(
            device_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

        device_parameter_key = device_key.GetSubkeyByName('Device Parameters')
        if device_parameter_key:
          event = time_events.DateTimeValuesEvent(
              device_parameter_key.last_written_time,
              definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        log_configuration_key = device_key.GetSubkeyByName('LogConf')
        if log_configuration_key:
          event = time_events.DateTimeValuesEvent(
              log_configuration_key.last_written_time,
              definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        properties_key = device_key.GetSubkeyByName('Properties')
        if properties_key:
          event = time_events.DateTimeValuesEvent(
              properties_key.last_written_time,
              definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(USBStorPlugin)
