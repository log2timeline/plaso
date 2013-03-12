#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Plug-in to format the Services and Drivers key with Start and Type values."""
from plaso.lib import event
from plaso.lib import win_registry_interface


class ServicesPlugin(win_registry_interface.ValuePlugin):
  """Plug-in to format the Services and Drivers keys having Type and Start."""

  REG_VALUES = frozenset(['Type', 'Start'])
  REG_TYPE = 'SYSTEM'
  URLS = ['http://support.microsoft.com/kb/103000']

  SERVICE_START = {
    0: 'Boot (0)',
    1: 'System (1)',
    2: 'Auto Start (2)',
    3: 'Manual (3)',
    4: 'Disabled (4)'
  }

  SERVICE_TYPE = {
    1: 'Kernel Device Driver (0x1)',
    2: 'File System Driver (0x2)',
    4: 'Adapter (0x4)',
    16: 'Service - Own Process (0x10)',
    32: 'Service - Share Process (0x20)'
  }

  SERVICE_ERROR = {
    0: 'Ignore (0)',
    1: 'Normal (1)',
    2: 'Severe (2)',
    3: 'Critical (3)'
  }

  OBJECT_NAME = ['localsystem', 'nt authority\\localservice',
                 'nt authority\\networkservice']

  def GetImagePath(self, subkey, service_type):
    """Returns the Image Path String with alerts for unusual settings.

    Returns Image Path with alerts for:
      Drivers having ImagePath outside system32/drivers.
      Services NOT having ImagePath.

    Args:
      subkey: Services subkey to format.
      service_type: Integer expressing the type of service or driver.

    Returns:
      None when Driver does not have an ImagePath.
      String when the ImagePath is set.
    """
    image_path = subkey.GetValue('ImagePath')
    if service_type > 0 and service_type < 15:
      if not image_path:
        return None
      image_path_str = image_path.GetStringData()
      if 'system32\\drivers' not in image_path_str.lower():
        return u'REGALERT Driver not in system32: {}'.format(image_path_str)
      return image_path_str
    elif service_type > 15 and service_type < 257:
      if image_path:
        # Add '' around Services Image path for readability of arguments.
        return '\'{}\''.format(image_path.GetStringData())
      return 'REGALERT: Service does not have ImagePath.'
    return None

  def GetObjectName(self, subkey, service_type):
    """Returns the ObjectName for Service with alerts for unusual settings.

    Alerts are for:
      Service with NO ObjectName.
      Service with unusual ObjectName.
      Driver with ObjectName.

    Args:
      subkey: The Services subkey to format.
      services_type: Integer expressing the type of service or driver.

    Returns:
      None when Driver does not have an ObjectName.
      String with ObjectName and alerts.
    """
    # Only Services should have ObjectName -- the "user" who started it.
    object_name = subkey.GetValue('ObjectName')
    # Handle Drivers first.  Alert if Driver has an ObjectName.
    if service_type > 0 and service_type < 15:
      if not object_name:
        return None
      return u'REGALERT Driver has ObjectName: {}'.format(
          object_name.GetStringData())
    elif service_type > 15 and service_type < 257:
      if not object_name:
        return u'REGALERT Service has no ObjectName'
      object_name_str = object_name.GetStringData()
      if object_name_str.lower() not in self.OBJECT_NAME:
        # There are 3 primary owners, all others are noteworthy.
        return u'REGALERT Unusual Owner: {}'.format(
            object_name_str)
    return None

  def GetEntries(self):
    """Create one event for each subkey under Services that has Type and Start.

    Adds descriptions of the ErrorControl, Type and StartvValues.
    Alerts on unusual settingssuch as Start/Type mismatches or drivers outside
    of C:/Windows/system32/drivers.
    """
    text_dict = {}
    service_type = self._key.GetValue('Type').GetData()
    service_start = self._key.GetValue('Start').GetData()

    service_type_str = self.SERVICE_TYPE.get(service_type, service_type)
    service_start_str = self.SERVICE_START.get(service_start, service_start)

    # Check for unusal Type/Start pairs.
    if service_type > 0 and service_type < 15 and service_start == 2:
      service_start_str = 'REGALERT Unusual Start for Driver: {}'.format(
          self.SERVICE_START[service_start])
    if service_type > 15 and service_type < 257 and service_start in [0,1]:
      service_start_str = 'REGALERT Unusal Start for Service: {}'.format(
          self.SERVICE_START[service_start])

    text_dict['Type'] = service_type_str
    text_dict['Start'] = service_start_str

    # Convert ErrorControl to Human Readable.
    if self._key.GetValue('ErrorControl'):
      error_control = self._key.GetValue('ErrorControl').GetData()
      text_dict['ErrorControl'] = self.SERVICE_ERROR.get(error_control,
                                                         error_control)

    object_name = self.GetObjectName(self._key, service_type)
    if object_name:
      text_dict['ObjectName'] = object_name

    image_path = self.GetImagePath(self._key, service_type)
    if image_path:
      text_dict['ImagePath'] = image_path

    # Gather all the other values and insert as they are.
    for value in self._key.GetValues():
      if value.name not in text_dict:
        text_dict[value.name] = value.GetData()

    event_object = event.WinRegistryEvent(self._key.path, text_dict,
                                          self._key.timestamp)
    yield event_object

