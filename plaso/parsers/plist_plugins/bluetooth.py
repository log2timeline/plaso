#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
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
"""This file contains a default plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class BluetoothPlugin(interface.PlistPlugin):
  """Basic plugin to extract interesting Bluetooth related keys."""

  NAME = 'plist_bluetooth'
  DESCRIPTION = u'Parser for Bluetooth plist files.'

  PLIST_PATH = 'com.apple.bluetooth.plist'
  PLIST_KEYS = frozenset(['DeviceCache', 'PairedDevices'])

  # LastInquiryUpdate = Device connected via Bluetooth Discovery.  Updated
  #   when a device is detected in discovery mode.  E.g. BT headphone power
  #   on.  Pairing is not required for a device to be discovered and cached.
  #
  # LastNameUpdate = When the human name was last set.  Usually done only once
  #   during initial setup.
  #
  # LastServicesUpdate = Time set when device was polled to determine what it
  #   is.  Usually done at setup or manually requested via advanced menu.

  def GetEntries(
      self, parser_context, file_entry=None, parser_chain=None, match=None,
      **unused_kwargs):
    """Extracts relevant BT entries.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      match: Optional dictionary containing extracted keys from PLIST_KEYS.
             The default is None.
    """
    root = '/DeviceCache'

    for device, value in match['DeviceCache'].items():
      name = value.get('Name', '')
      if name:
        name = u''.join(('Name:', name))

      if device in match['PairedDevices']:
        desc = 'Paired:True {0:s}'.format(name)
        key = device
        if 'LastInquiryUpdate' in value:
          event_object = plist_event.PlistEvent(
              root, key, value['LastInquiryUpdate'], desc)
          parser_context.ProduceEvent(
              event_object, parser_chain=parser_chain, file_entry=file_entry)

      if value.get('LastInquiryUpdate'):
        desc = u' '.join(filter(None, ('Bluetooth Discovery', name)))
        key = u''.join((device, '/LastInquiryUpdate'))
        event_object = plist_event.PlistEvent(
            root, key, value['LastInquiryUpdate'], desc)
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)

      if value.get('LastNameUpdate'):
        desc = u' '.join(filter(None, ('Device Name Set', name)))
        key = u''.join((device, '/LastNameUpdate'))
        event_object = plist_event.PlistEvent(
            root, key, value['LastNameUpdate'], desc)
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)

      if value.get('LastServicesUpdate'):
        desc = desc = u' '.join(filter(None, ('Services Updated', name)))
        key = ''.join((device, '/LastServicesUpdate'))
        event_object = plist_event.PlistEvent(
            root, key, value['LastServicesUpdate'], desc)
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)


plist.PlistParser.RegisterPlugin(BluetoothPlugin)
