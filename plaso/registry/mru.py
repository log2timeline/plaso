#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a simple MRU plugin for Plaso."""

from plaso.lib import event
from plaso.lib import win_registry_interface
from plaso.winreg import interface


class MRUPlugin(win_registry_interface.ValuePlugin):
  """A simple generic MRU plugin for entries with a MRUList."""

  REG_TYPE = 'any'
  REG_VALUES = frozenset(['MRUList', 'a'])
  URLS = [u'http://forensicartifacts.com/tag/mru/']

  def GetText(self, mru_entry):
    """Returns a unicode string extracted from key value.

    Args:
      mru_entry: The name of the MRU entry to be read, it should correspond
                 directly to a value name in the registry key.

    Returns:
      A unicode string containing extracted value from the registry value.
    """

    val = self._key.GetValue(mru_entry)
    if val:
      if val.GetTypeStr() == 'SZ' or val.GetTypeStr() == 'EXPAND_SZ':
        string = val.GetData()
      else:
        # TODO: refactor this, interface should not be directly invoked
        # this should be moved to a module factory class or equiv.
        string = interface.GetRegistryStringValue(
            val.GetRawData(), val.GetTypeStr())
      return string
    return u''

  def GetEntries(self):
    """Extract EventObjects from a MRU list."""
    mru_list_data = self._key.GetValue('MRUList')
    mru_list = mru_list_data.GetData()

    event_timestamp = self._key.timestamp

    for nr, entry in enumerate(mru_list):
      text_dict = {}
      text_dict[u'MRUList Entry %d' % (nr + 1)] = self.GetText(entry)
      evt = event.WinRegistryEvent(self._key.path, text_dict, event_timestamp)
      event_timestamp = 0
      evt.source_append = ': MRU List'
      yield evt

