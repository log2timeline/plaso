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

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class ServicesPlugin(interface.ValuePlugin):
  """Plug-in to format the Services and Drivers keys having Type and Start."""

  NAME = 'winreg_services'
  DESCRIPTION = u'Parser for services and drivers Registry data.'

  REG_VALUES = frozenset(['Type', 'Start'])
  REG_TYPE = 'SYSTEM'
  URLS = ['http://support.microsoft.com/kb/103000']


  def GetServiceDll(self, key):
    """Get the Service DLL for a service, if it exists.

    Checks for a ServiceDLL for in the Parameters subkey of a service key in
    the Registry.

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

  def GetEntries(
      self, parser_context, key=None, registry_type=None, file_entry=None,
      parser_chain=None, **unused_kwargs):
    """Create one event for each subkey under Services that has Type and Start.

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

    service_type_value = key.GetValue('Type')
    service_start_value = key.GetValue('Start')

    # Grab the ServiceDLL value if it exists.
    if service_type_value and service_start_value:
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

      # Create a specific service event, so that we can recognize and expand
      # certain values when we're outputting the event.
      event_object = windows_events.WindowsRegistryServiceEvent(
          key.last_written_timestamp, key.path, text_dict, offset=key.offset,
          registry_type=registry_type, urls=self.URLS)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)


winreg.WinRegistryParser.RegisterPlugin(ServicesPlugin)
