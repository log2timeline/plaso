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
"""This file contains a simple WinVersion plugin for Plaso."""

import struct

from plaso.lib import event
from plaso.lib import win_registry_interface


class WinVerPlugin(win_registry_interface.KeyPlugin):
  """Pulling information about the version of Windows."""

  REG_KEY = '\\Microsoft\\Windows NT\\CurrentVersion'
  REG_TYPE = 'SOFTWARE'
  URLS = []

  def GetText(self, value):
    """Return the text value from the registry key."""
    val = self._key.GetValue(value)
    if val:
      return val.GetStringData()

    return ''

  def GetEntries(self):
    """Gather minimal information about system install and return an event."""
    text_dict = {}
    text_dict[u'Owner'] = self.GetText('RegisteredOwner')
    text_dict[u'sp'] = self.GetText('CSDBuildNumber')
    text_dict[u'Product name'] = self.GetText('ProductName')
    text_dict[u' Windows Version Information'] = u''
    install_raw = self._key.GetValue('InstallDate').GetRawData()
    int_len = struct.calcsize('<I')
    if len(install_raw) < int_len:
      install = 0
    else:
      install = struct.unpack('<I', install_raw[:int_len])[0] * 1e6

    evt = event.RegistryEvent(self._key.path, text_dict, int(install))
    evt.prodname = text_dict[u'Product name']
    evt.source_long = 'SOFTWARE WinVersion key'
    if text_dict[u'Owner']:
      evt.owner = text_dict[u'Owner']
    yield evt

