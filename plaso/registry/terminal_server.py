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
"""This file contains the Terminal Server plugins."""
# TODO: add tests.

from plaso.lib import event
from plaso.lib import win_registry_interface


__author__ = 'David Nides (david.nides@gmail.com)'


class TerminalServerClientPlugin(win_registry_interface.KeyPlugin):
  """Base class for Terminal Server Client Connection plugins."""

  __abstract = True

  DESCRIPTION = 'RDP Connection'

  def GetEntries(self):
    """Collect Values in Servers and return event for each one."""
    for subkey in self._key.GetSubkeys():
      username_value = subkey.GetValue('UsernameHint')

      if (username_value and username_value.data and
          username_value.DataIsString()):
        username = username_value.data
      else:
        username = u'None'

      text_dict = {}
      text_dict['UsernameHint'] = username

      yield event.WinRegistryEvent(
          self._key.path, text_dict, timestamp=self._key.last_written_timestamp,
          source_append=': {0:s}'.format(self.DESCRIPTION))


class TerminalServerClientMRUPlugin(win_registry_interface.KeyPlugin):
  """Base class for Terminal Server Client Connection MRUs plugins."""

  __abstract = True

  DESCRIPTION = 'RDP Connection'

  def GetEntries(self):
    """Collect MRU Values and return event for each one."""
    for value in self._key.GetValues():
      # TODO: add a check for the value naming scheme.
      # Ignore the default value.
      if not value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      text_dict = {}
      text_dict[value.name] = value.data

      if value.name == 'MRU0':
        timestamp = self._key.last_written_timestamp
      else:
        timestamp = 0

      yield event.WinRegistryEvent(
          self._key.path, text_dict, timestamp=timestamp,
          source_append=': {0:s}'.format(self.DESCRIPTION))


class ServersTerminalServerClientPlugin(TerminalServerClientPlugin):
  """Gathers the Servers key for the User hive."""

  REG_KEY = '\\Software\\Microsoft\\Terminal Server Client\\Servers'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'RDP Connection'


class RDPDRTerminalServerClientPlugin(TerminalServerClientPlugin):
  """Gathers the RDPDR key for the User hive."""

  REG_KEY = ('\\Software\\Microsoft\\Terminal Server Client\\'
             'Default\\AddIns\\RDPDR')
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'RDP Connection'


class DefaulTerminalServerClientMRUPlugin(TerminalServerClientMRUPlugin):
  """Gathers the Default key for the User hive."""

  REG_KEY = '\\Software\\Microsoft\\Terminal Server Client\\Default'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'RDP Connection'


class LocalDevicesTerminalServerClientMRUPlugin(TerminalServerClientMRUPlugin):
  """Gathers the LocalDevices key for the User hive."""

  REG_KEY = '\\Software\\Microsoft\\Terminal Server Client\\LocalDevices'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'RDP Connection'
