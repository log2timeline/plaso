# -*- coding: utf-8 -*-

import logging

from plaso.events import windows_events
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class USBStorPlugin(interface.KeyPlugin):
  """USBStor key plugin."""

  NAME = 'winreg_usbstor'
  DESCRIPTION = u'Parser for USB storage Registry data.'

  REG_KEYS = [u'\\{current_control_set}\\Enum\\USBSTOR']
  REG_TYPE = 'SYSTEM'

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **kwargs):
    """Collect Values under USBStor and return an event object for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    for subkey in key.GetSubkeys():
      text_dict = {}
      text_dict[u'subkey_name'] = subkey.name

      # Time last USB device of this class was first inserted.
      event_object = windows_events.WindowsRegistryEvent(
          subkey.last_written_timestamp, key.path, text_dict,
          usage=eventdata.EventTimestamp.FIRST_CONNECTED, offset=key.offset,
          registry_type=registry_type,
          source_append=u': USBStor Entries')
      parser_mediator.ProduceEvent(event_object)

      name_values = subkey.name.split(u'&')
      number_of_name_values = len(name_values)

      # Normally we expect 4 fields here however that is not always the case.
      if number_of_name_values != 4:
        logging.warning(
            u'Expected 4 &-separated values in: {0:s}'.format(subkey.name))

      if number_of_name_values >= 1:
        text_dict[u'device_type'] = name_values[0]
      if number_of_name_values >= 2:
        text_dict[u'vendor'] = name_values[1]
      if number_of_name_values >= 3:
        text_dict[u'product'] = name_values[2]
      if number_of_name_values >= 4:
        text_dict[u'revision'] = name_values[3]

      for devicekey in subkey.GetSubkeys():
        text_dict[u'serial'] = devicekey.name

        friendly_name_value = devicekey.GetValue(u'FriendlyName')
        if friendly_name_value:
          text_dict[u'friendly_name'] = friendly_name_value.data
        else:
          text_dict.pop(u'friendly_name', None)

        # ParentIdPrefix applies to Windows XP Only.
        parent_id_prefix_value = devicekey.GetValue(u'ParentIdPrefix')
        if parent_id_prefix_value:
          text_dict[u'parent_id_prefix'] = parent_id_prefix_value.data
        else:
          text_dict.pop(u'parent_id_prefix', None)

        # Win7 - Last Connection.
        # Vista/XP - Time of an insert.
        event_object = windows_events.WindowsRegistryEvent(
            devicekey.last_written_timestamp, key.path, text_dict,
            usage=eventdata.EventTimestamp.LAST_CONNECTED, offset=key.offset,
            registry_type=registry_type,
            source_append=u': USBStor Entries')
        parser_mediator.ProduceEvent(event_object)

        # Build list of first Insertion times.
        first_insert = []
        device_parameter_key = devicekey.GetSubkey(u'Device Parameters')
        if device_parameter_key:
          first_insert.append(device_parameter_key.last_written_timestamp)

        log_configuration_key = devicekey.GetSubkey(u'LogConf')
        if (log_configuration_key and
            log_configuration_key.last_written_timestamp not in first_insert):
          first_insert.append(log_configuration_key.last_written_timestamp)

        properties_key = devicekey.GetSubkey(u'Properties')
        if (properties_key and
            properties_key.last_written_timestamp not in first_insert):
          first_insert.append(properties_key.last_written_timestamp)

        # Add first Insertion times.
        for timestamp in first_insert:
          event_object = windows_events.WindowsRegistryEvent(
              timestamp, key.path, text_dict,
              usage=eventdata.EventTimestamp.LAST_CONNECTED, offset=key.offset,
              registry_type=registry_type,
              source_append=u': USBStor Entries')
          parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(USBStorPlugin)
