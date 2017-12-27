# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the USB Device key."""

from __future__ import unicode_literals

import logging

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class USBPlugin(interface.WindowsRegistryPlugin):
  """USB Windows Registry plugin for last connection time."""

  NAME = 'windows_usb_devices'
  DESCRIPTION = 'Parser for USB device Registry entries.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum\\USB')])

  URLS = [
      ('https://msdn.microsoft.com/en-us/library/windows/hardware/'
       'jj649944%28v=vs.85%29.aspx')]

  _SOURCE_APPEND = ': USB Entries'

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

      vendor_identification = None
      product_identification = None
      try:
        subkey_name_parts = subkey.name.split('&')
        if len(subkey_name_parts) >= 2:
          vendor_identification = subkey_name_parts[0]
          product_identification = subkey_name_parts[1]
      except ValueError as exception:
        logging.warning(
            'Unable to split string: {0:s} with error: {1!s}'.format(
                subkey.name, exception))

      if vendor_identification and product_identification:
        values_dict['vendor'] = vendor_identification
        values_dict['product'] = product_identification

      for devicekey in subkey.GetSubkeys():
        values_dict['serial'] = devicekey.name

        event_data = windows_events.WindowsRegistryEventData()
        event_data.key_path = registry_key.path
        event_data.offset = registry_key.offset
        event_data.regvalue = values_dict
        event_data.source_append = self._SOURCE_APPEND

        # Last USB connection per USB device recorded in the Registry.
        event = time_events.DateTimeValuesEvent(
            devicekey.last_written_time,
            definitions.TIME_DESCRIPTION_LAST_CONNECTED)
        parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(USBPlugin)
