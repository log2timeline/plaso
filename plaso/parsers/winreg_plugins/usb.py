#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains the USB key plugin."""

import logging

from plaso.events import windows_events
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class USBPlugin(interface.KeyPlugin):
  """USB Windows Registry plugin for last connection time."""

  NAME = 'winreg_usb'
  DESCRIPTION = u'Parser for USB storage Registry data.'

  REG_KEYS = [u'\\{current_control_set}\\Enum\\USB']
  REG_TYPE = 'SYSTEM'

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **kwargs):
    """Collect SubKeys under USB and produce an event object for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    for subkey in key.GetSubkeys():
      text_dict = {}
      text_dict['subkey_name'] = subkey.name

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
        text_dict['vendor'] = vendor_identification
        text_dict['product'] = product_identification

      for devicekey in subkey.GetSubkeys():
        text_dict['serial'] = devicekey.name

        # Last USB connection per USB device recorded in the Registry.
        event_object = windows_events.WindowsRegistryEvent(
            devicekey.last_written_timestamp, key.path, text_dict,
            usage=eventdata.EventTimestamp.LAST_CONNECTED, offset=key.offset,
            registry_type=registry_type,
            source_append=': USB Entries')
        parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(USBPlugin)
