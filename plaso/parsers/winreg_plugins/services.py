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
"""Plug-in to format the Services and Drivers key with Start and Type values."""

from plaso.lib import event
from plaso.parsers.winreg_plugins import interface


class ServicesPlugin(interface.ValuePlugin):
  """Plug-in to format the Services and Drivers keys having Type and Start."""

  NAME = 'winreg_services'

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

  OBJECT_NAMES = [
      'localsystem', 'nt authority\\localservice',
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
      A Unicode string when the ImagePath value is set in service.
      A driver does not have an ImagePath so None is returned.
      A REGALERT Unicode string is returned when an anomaly is detected.
    """
    image_path = subkey.GetValue('ImagePath')

    if service_type > 0 and service_type < 15:
      if not image_path:
        return None

      # TODO: Remove RegAlert completely
      # if not image_path.data or not image_path.DataIsString():
        # return 'REGALERT: Driver does not have a valid ImagePath.'

      image_path_str = image_path.data
      # if 'system32\\drivers' not in image_path_str.lower():
        # return u'REGALERT Driver not in system32: {}'.format(image_path_str)
      return image_path_str


    # elif service_type > 15 and service_type < 257:
      # if not image_path:
        # return 'REGALERT: Service does not have ImagePath.'

      # if not image_path.data or not image_path.DataIsString():
        # return 'REGALERT: Service does not have a valid ImagePath.'

      # return u'\'{}\''.format(image_path.data)
    return None

  # TODO: Remove service_type when RegAlert goes away
  def GetObjectName(self, subkey, unused_service_type):
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
    if object_name and object_name.data and object_name.DataIsString():
      return object_name.data
    else:
      return None
    # TODO: Remove RegAlert completely
    # Handle Drivers first.  Alert if Driver has an ObjectName.
    # if service_type > 0 and service_type < 15:
      # if not object_name:
        # return None

      # if object_name.data and object_name.DataIsString():
        # object_name_str = object_name.data
      # else:
        # object_name_str = u'UNKNOWN'

      # return u'REGALERT Driver has ObjectName: {}'.format(
          # object_name_str)

    # elif service_type > 15 and service_type < 257:
      # if not object_name:
        # return u'REGALERT Service does not have ObjectName'

      # if not object_name.data or not object_name.DataIsString():
        # return u'REGALERT Service does not have a valid ObjectName'

      # object_name_str = object_name.data
      # if object_name_str.lower() not in self.OBJECT_NAMES:
        # There are 3 primary owners, all others are noteworthy.
        # return u'REGALERT Unusual Owner: {}'.format(
            # object_name_str)
    # return None

  def GetServiceDll(self, key):
    """Get the Service DLL for a service, if it exists.

    Checks for a ServiceDLL for a service key.

    Args:
      key: A Windows Registry key (instance of WinRegKey).
    """
    parameters_key = key.GetSubkey('Parameters')
    if parameters_key:
      service_dll = parameters_key.GetValue('ServiceDll')
      if service_dll:
        return service_dll.data
    else:
      return None

  def GetEntries(self, unused_parser_context, key=None, **unused_kwargs):
    """Create one event for each subkey under Services that has Type and Start.

    Adds descriptions of the ErrorControl, Type and Start Values.
    Alerts on unusual settings such as Start/Type mismatches or drivers outside
    of C:/Windows/system32/drivers.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: A Windows Registry key (instance of WinRegKey).

    Yields:
      Event objects extracted from the Windows service values.
    """
    text_dict = {}

    service_type_value = key.GetValue('Type')
    service_start_value = key.GetValue('Start')

    if service_type_value and service_start_value:
      service_type = service_type_value.data
      text_dict['Type'] = self.SERVICE_TYPE.get(service_type, service_type)

      service_start = service_start_value.data
      service_start_str = self.SERVICE_START.get(service_start, service_start)

      # TODO: Remove RegAlert completely
      # Check for unusal Type/Start pairs.
      # if service_type > 0 and service_type < 15 and service_start == 2:
        # service_start_str = 'REGALERT Unusual Start for Driver: {}'.format(
            # self.SERVICE_START[service_start])

      # if service_type > 15 and service_type < 257 and service_start in [0, 1]:
        # service_start_str = 'REGALERT Unusal Start for Service: {}'.format(
            # self.SERVICE_START[service_start])

      text_dict['Start'] = service_start_str

      # Convert ErrorControl to Human Readable.
      if key.GetValue('ErrorControl'):
        error_control = key.GetValue('ErrorControl').data
        text_dict['ErrorControl'] = self.SERVICE_ERROR.get(
            error_control, error_control)

      object_name = self.GetObjectName(key, service_type)
      if object_name:
        text_dict['ObjectName'] = object_name

      image_path = self.GetImagePath(key, service_type)
      if image_path:
        text_dict['ImagePath'] = image_path

      service_dll = self.GetServiceDll(key)
      if service_dll:
        text_dict['ServiceDll'] = service_dll

      # Gather all the other string and integer values and insert as they are.
      for value in key.GetValues():
        if not value.name:
          continue
        if value.name not in text_dict:
          if value.DataIsString() or value.DataIsInteger():
            text_dict[value.name] = value.data
          elif value.DataIsMultiString():
            text_dict[value.name] = u', '.join(value.data)

      event_object = event.WinRegistryEvent(
          key.path, text_dict, timestamp=key.last_written_timestamp)
      yield event_object
