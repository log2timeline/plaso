#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""This file contains the USBStor keys plugins."""

import logging

from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class USBStorPlugin(interface.KeyPlugin):
  """USBStor key plugin."""

  NAME = 'winreg_usbstor'

  REG_KEYS = [u'\\{current_control_set}\\Enum\\USBSTOR']
  REG_TYPE = 'SYSTEM'
  DESCRIPTION = 'USBStor Entries'

  def GetEntries(self, unused_cache=None):
    """Collect Values under USBStor and return an event object for each one."""
    for subkey in self._key.GetSubkeys():

      text_dict = {}
      text_dict['subkey_name'] = subkey.name

      # Time last USB device of this class was first inserted.
      yield event.WinRegistryEvent(
          self._key.path, text_dict, timestamp=subkey.last_written_timestamp,
          usage=eventdata.EventTimestamp.FIRST_CONNECTED,
          source_append=': {0:s}'.format(self.DESCRIPTION))

      # TODO: Determine if these 4 fields always exist.
      try:
        device_type, vendor, product, revision = subkey.name.split('&')
      except ValueError as exception:
        logging.warning(
            u'Unable to split string: {} - [{}]'.format(
              subkey.name, exception))

      text_dict['device_type'] = device_type
      text_dict['vendor'] = vendor
      text_dict['product'] = product
      text_dict['revision'] = revision

      for devicekey in subkey.GetSubkeys():
        text_dict['serial'] = devicekey.name

        friendly_name_value = devicekey.GetValue('FriendlyName')
        if friendly_name_value:
          text_dict['friendly_name'] = friendly_name_value.data
        else:
          text_dict.pop('friendly_name', None)

        # ParentIdPrefix applies to Windows XP Only.
        parent_id_prefix_value = devicekey.GetValue('ParentIdPrefix')
        if parent_id_prefix_value:
          text_dict['parent_id_prefix'] = parent_id_prefix_value.data
        else:
          text_dict.pop('parent_id_prefix', None)

        # Win7 - Last Connection.
        # Vista/XP - Time of an insert.
        yield event.WinRegistryEvent(
            self._key.path, text_dict,
            timestamp=devicekey.last_written_timestamp,
            usage=eventdata.EventTimestamp.LAST_CONNECTED,
            source_append=': {0:s}'.format(self.DESCRIPTION))

        # Build list of first Insertion times.
        first_insert = []
        device_parameter_key = devicekey.GetSubkey('Device Parameters')
        if device_parameter_key:
          first_insert.append(device_parameter_key.last_written_timestamp)

        log_configuration_key = devicekey.GetSubkey('LogConf')
        if (log_configuration_key and
            log_configuration_key.last_written_timestamp not in first_insert):
          first_insert.append(log_configuration_key.last_written_timestamp)

        properties_key = devicekey.GetSubkey('Properties')
        if (properties_key and
            properties_key.last_written_timestamp not in first_insert):
          first_insert.append(properties_key.last_written_timestamp)

        # Add first Insertion times.
        for timestamp in first_insert:
          yield event.WinRegistryEvent(
              self._key.path, text_dict, timestamp=timestamp,
              usage=eventdata.EventTimestamp.LAST_CONNECTED,
              source_append=': {0:s}'.format(self.DESCRIPTION))
