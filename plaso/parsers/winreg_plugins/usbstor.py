# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the USBStor key."""

import logging

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class USBStorPlugin(interface.WindowsRegistryPlugin):
  """USBStor key plugin."""

  NAME = u'windows_usbstor_devices'
  DESCRIPTION = u'Parser for USB Plug And Play Manager USBStor Registry Key.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum\\USBSTOR')])

  URLS = [u'http://www.forensicswiki.org/wiki/USB_History_Viewing']

  _SOURCE_APPEND = u': USBStor Entries'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for subkey in registry_key.GetSubkeys():
      values_dict = {}
      values_dict[u'subkey_name'] = subkey.name

      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = registry_key.path
      event_data.offset = registry_key.offset
      event_data.regvalue = values_dict
      event_data.source_append = self._SOURCE_APPEND

      # Time last USB device of this class was first inserted.
      event = time_events.DateTimeValuesEvent(
          subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      name_values = subkey.name.split(u'&')
      number_of_name_values = len(name_values)

      # Normally we expect 4 fields here however that is not always the case.
      if number_of_name_values != 4:
        logging.warning(
            u'Expected 4 &-separated values in: {0:s}'.format(subkey.name))

      if number_of_name_values >= 1:
        values_dict[u'device_type'] = name_values[0]
      if number_of_name_values >= 2:
        values_dict[u'vendor'] = name_values[1]
      if number_of_name_values >= 3:
        values_dict[u'product'] = name_values[2]
      if number_of_name_values >= 4:
        values_dict[u'revision'] = name_values[3]

      for device_key in subkey.GetSubkeys():
        values_dict[u'serial'] = device_key.name

        friendly_name_value = device_key.GetValueByName(u'FriendlyName')
        if friendly_name_value:
          values_dict[u'friendly_name'] = friendly_name_value.GetDataAsObject()
        else:
          values_dict.pop(u'friendly_name', None)

        # ParentIdPrefix applies to Windows XP Only.
        parent_id_prefix_value = device_key.GetValueByName(u'ParentIdPrefix')
        if parent_id_prefix_value:
          values_dict[u'parent_id_prefix'] = (
              parent_id_prefix_value.GetDataAsObject())
        else:
          values_dict.pop(u'parent_id_prefix', None)

        # Win7 - Last Connection.
        # Vista/XP - Time of an insert.
        event = time_events.DateTimeValuesEvent(
            device_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

        device_parameter_key = device_key.GetSubkeyByName(u'Device Parameters')
        if device_parameter_key:
          event = time_events.DateTimeValuesEvent(
              device_parameter_key.last_written_time,
              definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        log_configuration_key = device_key.GetSubkeyByName(u'LogConf')
        if log_configuration_key:
          event = time_events.DateTimeValuesEvent(
              log_configuration_key.last_written_time,
              definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        properties_key = device_key.GetSubkeyByName(u'Properties')
        if properties_key:
          event = time_events.DateTimeValuesEvent(
              properties_key.last_written_time,
              definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(USBStorPlugin)
