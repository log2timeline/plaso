#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains the RDP Connections plugin for Plaso."""


from plaso.lib import event
from plaso.lib import win_registry_interface


__author__ = 'David Nides (david.nides@gmail.com)'


class RDP(win_registry_interface.KeyPlugin):
  """Base class for all RDP Connections Key plugins."""

  __abstract = True


  DESCRIPTION = 'RDP Connetion'


  def GetEntries(self):
    """Collect Values in Servers and return event for each one."""
    for subkey in self._key.GetSubkeys():
      if not subkey.name:
        continue
      for value in subkey.GetValues():
        username_value = subkey.GetValue('UsernameHint')
        if username_value:
          username = username_value.GetStringData()
        else:
          username = 'None'
      text_dict = {}
      text_dict[value.name] = username
      
      if not text_dict[value.name]:
        continue

      reg_evt = event.WinRegistryEvent(
          self._key.path, text_dict, self._key.timestamp)

      reg_evt.source_append = ': {}'.format(self.DESCRIPTION)
      yield reg_evt


class RDPMRU(win_registry_interface.KeyPlugin):
  """Base class for all RDP Connection MRUs plugins."""

  __abstract = True

  DESCRIPTION = 'RDP Connection'

  def GetEntries(self):
    """Collect MRU Values and return event for each one."""
    for value in self._key.GetValues():
      text_dict = {}
      data = value.GetStringData()
      if not data:
        continue
      text_dict[value.name] = data

      if value.name == 'MRU0':
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict, self._key.timestamp)
      else:
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict, 0)

      reg_evt.source_append = ': {}'.format(self.DESCRIPTION)
      yield reg_evt
      

class ServerPlugin(RDP):
  """Gathers the Servers key for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Terminal Server Client\\Servers'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'RDP Connection'


class RDPDRPlugin(RDP):
  """Gathers the RDPDR key for the NTUSER hive."""

  REG_KEY = ('\\Software\\Microsoft\\Terminal Server Client\\',
             'Default\\AddIns\\RDPDR')
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'RDP Connection'


class DefaultPlugin(RDPMRU):
  """Gathers the Default key for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Terminal Server Client\\Default'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'RDP Connection'


class LocalDevicesPlugin(RDPMRU):
  """Gathers the LocalDevices key for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Terminal Server Client\\LocalDevices'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'RDP Connection'
