# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the USBStor key."""

import logging

from plaso.containers import windows_events
from plaso.lib import eventdata
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

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Collect Values under USBStor and return an event object for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    for subkey in registry_key.GetSubkeys():
      values_dict = {}
      values_dict[u'subkey_name'] = subkey.name

      # Time last USB device of this class was first inserted.
      event_object = windows_events.WindowsRegistryEvent(
          subkey.last_written_time, registry_key.path, values_dict,
          offset=registry_key.offset, source_append=self._SOURCE_APPEND,
          usage=eventdata.EventTimestamp.FIRST_CONNECTED)
      parser_mediator.ProduceEvent(event_object)

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

      for devicekey in subkey.GetSubkeys():
        values_dict[u'serial'] = devicekey.name

        friendly_name_value = devicekey.GetValueByName(u'FriendlyName')
        if friendly_name_value:
          values_dict[u'friendly_name'] = friendly_name_value.GetDataAsObject()
        else:
          values_dict.pop(u'friendly_name', None)

        # ParentIdPrefix applies to Windows XP Only.
        parent_id_prefix_value = devicekey.GetValueByName(u'ParentIdPrefix')
        if parent_id_prefix_value:
          values_dict[u'parent_id_prefix'] = (
              parent_id_prefix_value.GetDataAsObject())
        else:
          values_dict.pop(u'parent_id_prefix', None)

        # Win7 - Last Connection.
        # Vista/XP - Time of an insert.
        event_object = windows_events.WindowsRegistryEvent(
            devicekey.last_written_time, registry_key.path, values_dict,
            offset=registry_key.offset, source_append=self._SOURCE_APPEND,
            usage=eventdata.EventTimestamp.LAST_CONNECTED)
        parser_mediator.ProduceEvent(event_object)

        # Build list of first Insertion times.
        first_insert = []
        device_parameter_key = devicekey.GetSubkeyByName(u'Device Parameters')
        if device_parameter_key:
          first_insert.append(device_parameter_key.last_written_time)

        log_configuration_key = devicekey.GetSubkeyByName(u'LogConf')
        if (log_configuration_key and
            log_configuration_key.last_written_time not in first_insert):
          first_insert.append(log_configuration_key.last_written_time)

        properties_key = devicekey.GetSubkeyByName(u'Properties')
        if (properties_key and
            properties_key.last_written_time not in first_insert):
          first_insert.append(properties_key.last_written_time)

        # Add first Insertion times.
        for timestamp in first_insert:
          event_object = windows_events.WindowsRegistryEvent(
              timestamp, registry_key.path, values_dict,
              offset=registry_key.offset, source_append=self._SOURCE_APPEND,
              usage=eventdata.EventTimestamp.LAST_CONNECTED)
          parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(USBStorPlugin)
