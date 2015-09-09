# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the USB Device key."""

import logging

from plaso.events import windows_events
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class USBPlugin(interface.WindowsRegistryPlugin):
  """USB Windows Registry plugin for last connection time."""

  NAME = u'windows_usb_devices'
  DESCRIPTION = u'Parser for USB device Registry entries.'

  REG_KEYS = [u'\\{current_control_set}\\Enum\\USB']
  REG_TYPE = u'SYSTEM'

  URLS = [
      (u'https://msdn.microsoft.com/en-us/library/windows/hardware/'
       u'jj649944%28v=vs.85%29.aspx')]

  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **kwargs):
    """Collect SubKeys under USB and produce an event object for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of dfwinreg.WinRegistryKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    for subkey in key.GetSubkeys():
      text_dict = {}
      text_dict[u'subkey_name'] = subkey.name

      vendor_identification = None
      product_identification = None
      try:
        subkey_name_parts = subkey.name.split(u'&')
        if len(subkey_name_parts) >= 2:
          vendor_identification = subkey_name_parts[0]
          product_identification = subkey_name_parts[1]
      except ValueError as exception:
        logging.warning(
            u'Unable to split string: {0:s} with error: {1:s}'.format(
                subkey.name, exception))

      if vendor_identification and product_identification:
        text_dict[u'vendor'] = vendor_identification
        text_dict[u'product'] = product_identification

      for devicekey in subkey.GetSubkeys():
        text_dict[u'serial'] = devicekey.name

        # Last USB connection per USB device recorded in the Registry.
        event_object = windows_events.WindowsRegistryEvent(
            devicekey.last_written_time, key.path, text_dict, offset=key.offset,
            usage=eventdata.EventTimestamp.LAST_CONNECTED,
            registry_file_type=registry_file_type,
            source_append=u': USB Entries')
        parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(USBPlugin)
