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
"""This file contains the Terminal Server Registry plugins."""

from plaso.lib import event
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class TerminalServerClientPlugin(interface.KeyPlugin):
  """Windows Registry plugin for Terminal Server Client Connection keys."""

  NAME = 'winreg_rdp'
  DESCRIPTION = 'RDP Connection'

  REG_TYPE = 'NTUSER'
  REG_KEYS = [
      u'\\Software\\Microsoft\\Terminal Server Client\\Servers',
      u'\\Software\\Microsoft\\Terminal Server Client\\Default\\AddIns\\RDPDR']

  def GetEntries(self, unused_cache=None):
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


class TerminalServerClientMRUPlugin(interface.KeyPlugin):
  """Windows Registry plugin for Terminal Server Client Connection MRUs keys."""

  NAME = 'winreg_rdp_mru'

  DESCRIPTION = 'RDP Connection'

  REG_TYPE = 'NTUSER'
  REG_KEYS = [
      u'\\Software\\Microsoft\\Terminal Server Client\\Default',
      u'\\Software\\Microsoft\\Terminal Server Client\\LocalDevices']

  def GetEntries(self, unused_cache=None):
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
          source_append=u': {0:s}'.format(self.DESCRIPTION))
