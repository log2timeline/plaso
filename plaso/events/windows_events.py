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
