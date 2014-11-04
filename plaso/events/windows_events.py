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
"""This file contains the Windows specific event object classes."""

from plaso.events import time_events
from plaso.lib import eventdata


class WindowsVolumeCreationEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows volume creation event."""

  DATA_TYPE = 'windows:volume:creation'

  def __init__(self, filetime, device_path, serial_number, origin):
    """Initializes an event object.

    Args:
      filetime: The FILETIME timestamp value.
      device_path: A string containing the volume device path.
      serial_number: A string containing the volume serial number.
      origin: A string containing the origin of the event (event source).
    """
    super(WindowsVolumeCreationEvent, self).__init__(
        filetime, eventdata.EventTimestamp.CREATION_TIME)

    self.device_path = device_path
    self.serial_number = serial_number
    self.origin = origin


class WindowsRegistryEvent(time_events.TimestampEvent):
  """Convenience class for a Windows Registry-based event."""

  DATA_TYPE = 'windows:registry:key_value'

  def __init__(
      self, timestamp, key_name, value_dict, usage=None, offset=None,
      registry_type=None, urls=None, source_append=None):
    """Initializes a Windows registry event.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      key_name: The name of the Registry key being parsed.
      value_dict: The interpreted value of the key, stored as a dictionary.
      usage: Optional description of the usage of the time value.
             The default is None.
      offset: Optional (data) offset of the Registry key or value.
              The default is None.
      registry_type: Optional Registry type string. The default is None.
      urls: Optional list of URLs. The default is None.
      source_append: Optional string to append to the source_long of the event.
                     The default is None.
    """
    if usage is None:
      usage = eventdata.EventTimestamp.WRITTEN_TIME

    super(WindowsRegistryEvent, self).__init__(timestamp, usage)

    if key_name:
      self.keyname = key_name

    self.regvalue = value_dict

    if offset or type(offset) in [int, long]:
      self.offset = offset

    if registry_type:
      self.registry_type = registry_type

    if urls:
      self.url = u' - '.join(urls)

    if source_append:
      self.source_append = source_append


class WindowsRegistryServiceEvent(WindowsRegistryEvent):
  """Convenience class for service entries retrieved from the registry."""
  DATA_TYPE = 'windows:registry:service'
