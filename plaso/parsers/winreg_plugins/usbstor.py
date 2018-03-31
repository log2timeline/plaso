# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the USBStor key."""

from __future__ import unicode_literals

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class USBStorPlugin(interface.WindowsRegistryPlugin):
  """USBStor key plugin."""

  NAME = 'windows_usbstor_devices'
  DESCRIPTION = 'Parser for USB Plug And Play Manager USBStor Registry Key.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum\\USBSTOR')])

  URLS = ['http://www.forensicswiki.org/wiki/USB_History_Viewing']

  _SOURCE_APPEND = ': USBStor Entries'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for subkey in registry_key.GetSubkeys():
      values_dict = {}
      values_dict['subkey_name'] = subkey.name

      name_values = subkey.name.split('&')
      number_of_name_values = len(name_values)

      # Normally we expect 4 fields here however that is not always the case.
      if number_of_name_values != 4:
        logger.warning(
            'Expected 4 &-separated values in: {0:s}'.format(subkey.name))

      if number_of_name_values >= 1:
        values_dict['device_type'] = name_values[0]
      if number_of_name_values >= 2:
        values_dict['vendor'] = name_values[1]
      if number_of_name_values >= 3:
        values_dict['product'] = name_values[2]
      if number_of_name_values >= 4:
        values_dict['revision'] = name_values[3]

      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = registry_key.path
      event_data.offset = registry_key.offset
      event_data.regvalue = values_dict
      event_data.source_append = self._SOURCE_APPEND

      if subkey.number_of_subkeys == 0:
        # Time last USB device of this class was first inserted.
        event = time_events.DateTimeValuesEvent(
            subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)
        continue

      for device_key in subkey.GetSubkeys():
        values_dict['serial'] = device_key.name

        friendly_name_value = device_key.GetValueByName('FriendlyName')
        if friendly_name_value:
          values_dict['friendly_name'] = friendly_name_value.GetDataAsObject()
        else:
          values_dict.pop('friendly_name', None)

        # ParentIdPrefix applies to Windows XP Only.
        parent_id_prefix_value = device_key.GetValueByName('ParentIdPrefix')
        if parent_id_prefix_value:
          values_dict['parent_id_prefix'] = (
              parent_id_prefix_value.GetDataAsObject())
        else:
          values_dict.pop('parent_id_prefix', None)

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
