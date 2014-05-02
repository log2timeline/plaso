#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""This file contains a plist plugin for the iPod/iPhone storage plist."""

from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers.plist_plugins import interface


class IPodPlistEvent(event.PythonDatetimeEvent):
  """An event object for an entry in the iPod plist file."""

  DATA_TYPE = 'ipod:device:entry'

  def __init__(self, datetime_timestamp, device_id, device_info):
    """Initialize the event.

    Args:
      datetime_timestamp: The timestamp for the event as a datetime object.
      device_id: The device ID.
      device_info: A dict that contains extracted information from the plist.
    """
    super(IPodPlistEvent, self).__init__(
        datetime_timestamp, eventdata.EventTimestamp.LAST_CONNECTED)

    self.device_id = device_id

    # Save the other attributes.
    for key, value in device_info.iteritems():
      if key == 'Connected':
        continue
      attribute_name = key.lower().replace(u' ', u'_')
      setattr(self, attribute_name, value)


class IPodPlugin(interface.PlistPlugin):
  """Plugin to extract iPod/iPad/iPhone device information."""

  NAME = 'ipod_device'

  PLIST_PATH = 'com.apple.iPod.plist'
  PLIST_KEYS = frozenset(['Devices'])

  def GetEntries(self, match, **unused_kwargs):
    """Extract device information from the iPod plist.

    Args:
      match: A dictionary containing keys extracted from PLIST_KEYS.

    Yields:
      An event object (instance of IPodPlistEvent) extracted from the plist.
    """
    if not 'Devices' in match:
      return

    devices = match['Devices']
    if not devices:
      return

    for device, device_info in devices.iteritems():
      if 'Connected' not in device_info:
        continue
      yield IPodPlistEvent(device_info.get('Connected'), device, device_info)
