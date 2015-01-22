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
"""Formatter for service entries derived from Windows Registry files."""

from plaso.formatters import manager
from plaso.formatters import winreg
from plaso.winnt import human_readable_service_enums


class WinRegistryServiceFormatter(winreg.WinRegistryGenericFormatter):
  """Formatter for a Windows service event extracted from the Registry."""

  DATA_TYPE = 'windows:registry:service'

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from the event object.

    This formatter will make the values of certain service parameters more
    readable by humans.

    Args:
      event_object: The event object (an instance of EventObject) containing
      the event specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    regvalue = getattr(event_object, 'regvalue', {})
    # Loop over all the registry value names in the service key.
    for service_value_name in regvalue.keys():
      # A temporary variable so we can refer to this long name more easily.
      service_enums = human_readable_service_enums.SERVICE_ENUMS
      # Check if we need to can make the value more human readable.
      if service_value_name in service_enums.keys():
        service_enum = service_enums[service_value_name]
        # Find the human readable version of the name and fall back to the
        # raw value if it's not found.
        human_readable_value = service_enum.get(
            regvalue[service_value_name],
            regvalue[service_value_name])
        regvalue[service_value_name] = human_readable_value

    return super(WinRegistryServiceFormatter, self).GetMessages(event_object)


manager.FormattersManager.RegisterFormatter(WinRegistryServiceFormatter)
