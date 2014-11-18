#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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

from plaso.events import windows_events
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WinVerPlugin(interface.KeyPlugin):
  """Plug-in to collect information about the Windows version."""

  NAME = 'winreg_winver'
  DESCRIPTION = u'Parser for Windows version Registry data.'

  REG_KEYS = [u'\\Microsoft\\Windows NT\\CurrentVersion']
  REG_TYPE = 'SOFTWARE'
  URLS = []

  INT_STRUCT = construct.ULInt32('install')

  # TODO: Refactor remove this function in a later CL.
  def GetValueString(self, key, value_name):
    """Retrieves a specific string value from the Registry key.

    Args:
      key: A Windows Registry key (instance of WinRegKey).
      value_name: The name of the value.

    Returns:
      A string value if one is available, otherwise an empty string.
    """
    value = key.GetValue(value_name)

    if not value:
      return ''

    if not value.data or not value.DataIsString():
      return ''
    return value.data

  def GetEntries(
      self, parser_context, key=None, registry_type=None, file_entry=None,
      parser_chain=None, **unused_kwargs):
    """Gather minimal information about system install and return an event.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
    """
    text_dict = {}
    text_dict[u'Owner'] = self.GetValueString(key, 'RegisteredOwner')
    text_dict[u'sp'] = self.GetValueString(key, 'CSDBuildNumber')
    text_dict[u'Product name'] = self.GetValueString(key, 'ProductName')
    text_dict[u' Windows Version Information'] = u''

    install_raw = key.GetValue('InstallDate').raw_data
    # TODO: move this to a function in utils with a more descriptive name
    # e.g. CopyByteStreamToInt32BigEndian.
    try:
      install = self.INT_STRUCT.parse(install_raw)
    except construct.FieldError:
      install = 0

    event_object = windows_events.WindowsRegistryEvent(
        timelib.Timestamp.FromPosixTime(install), key.path, text_dict,
        usage='OS Install Time', offset=key.offset,
        registry_type=registry_type, urls=self.URLS)

    event_object.prodname = text_dict[u'Product name']
    event_object.source_long = 'SOFTWARE WinVersion key'
    if text_dict[u'Owner']:
      event_object.owner = text_dict[u'Owner']
    parser_context.ProduceEvent(
        event_object, parser_chain=parser_chain, file_entry=file_entry)


winreg.WinRegistryParser.RegisterPlugin(WinVerPlugin)
