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
"""Plug-in to collect information about the Windows version."""
import construct

from plaso.lib import event
from plaso.lib import timelib
from plaso.lib import win_registry_interface


class WinVerPlugin(win_registry_interface.KeyPlugin):
  """Plug-in to collect information about the Windows version."""

  REG_KEY = '\\Microsoft\\Windows NT\\CurrentVersion'
  REG_TYPE = 'SOFTWARE'
  URLS = []

  INT_STRUCT = construct.ULInt32('install')

  # TODO: refactor remove this function in a later CL.
  def GetValueString(self, value_name):
    """Retrieves a specific string value from the Registry key.

    Args:
      value_name: The name of the value.

    Returns:
      A string containing the value data if the value data is
      a string type otherwise an empty string.
    """
    value = self._key.GetValue(value_name)

    if not value.data or not value.DataIsString():
      return ''
    return value.data

  def GetEntries(self):
    """Gather minimal information about system install and return an event."""
    text_dict = {}
    text_dict[u'Owner'] = self.GetValueString('RegisteredOwner')
    text_dict[u'sp'] = self.GetValueString('CSDBuildNumber')
    text_dict[u'Product name'] = self.GetValueString('ProductName')
    text_dict[u' Windows Version Information'] = u''
    install_raw = self._key.GetValue('InstallDate').GetRawData()
    # TODO: move this to a function in utils with a more descriptive name
    # e.g. CopyByteStreamToInt32BigEndian.
    try:
      install = self.INT_STRUCT.parse(install_raw)
    except construct.FieldError:
      install = 0

    event_object = event.WinRegistryEvent(
        self._key.path, text_dict,
        timestamp=timelib.Timestamp.FromPosixTime(install))
    event_object.prodname = text_dict[u'Product name']
    event_object.source_long = 'SOFTWARE WinVersion key'
    if text_dict[u'Owner']:
      event_object.owner = text_dict[u'Owner']
    yield event_object
