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
"""Plug-in to collect the Less Frequently Used Keys."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class BootVerificationPlugin(interface.KeyPlugin):
  """Plug-in to collect the Boot Verification Key."""

  NAME = 'winreg_boot_verify'
  DESCRIPTION = u'Parser for Boot Verification Registry data.'

  REG_TYPE = 'SYSTEM'
  REG_KEYS = [u'\\{current_control_set}\\Control\\BootVerificationProgram']

  URLS = ['http://technet.microsoft.com/en-us/library/cc782537(v=ws.10).aspx']

  def GetEntries(
      self, parser_context, key=None, registry_type=None, **unused_kwargs):
    """Gather the BootVerification key values and return one event for all.

    This key is rare, so its presence is suspect.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    text_dict = {}
    for value in key.GetValues():
      text_dict[value.name] = value.data
    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_timestamp, key.path, text_dict, offset=key.offset,
        registry_type=registry_type, urls=self.URLS)
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)


class BootExecutePlugin(interface.KeyPlugin):
  """Plug-in to collect the BootExecute Value from the Session Manager key."""

  NAME = 'winreg_boot_execute'
  DESCRIPTION = u'Parser for Boot Execution Registry data.'

  REG_TYPE = 'SYSTEM'
  REG_KEYS = [u'\\{current_control_set}\\Control\\Session Manager']

  URLS = ['http://technet.microsoft.com/en-us/library/cc963230.aspx']

  def GetEntries(
      self, parser_context, file_entry=None, key=None, registry_type=None,
      **unused_kwargs):
    """Gather the BootExecute Value, compare to default, return event.

    The rest of the values in the Session Manager key are in a separate event.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    text_dict = {}

    for value in key.GetValues():
      if value.name == 'BootExecute':
        # MSDN: claims that the data type of this value is REG_BINARY
        # although REG_MULTI_SZ is known to be used as well.
        if value.DataIsString():
          value_string = value.data
        elif value.DataIsMultiString():
          value_string = u''.join(value.data)
        elif value.DataIsBinaryData():
          value_string = value.data
        else:
          value_string = u''
          error_string = (
              u'Key: {0:s}, value: {1:s}: unuspported value data type: '
              u'{2:s}.').format(key.path, value.name, value.data_type_string)
          parser_context.ProduceParseError(
              self.NAME, error_string, file_entry=file_entry)

        # TODO: why does this have a separate event object? Remove this.
        value_dict = {'BootExecute': value_string}
        event_object = windows_events.WindowsRegistryEvent(
            key.last_written_timestamp, key.path, value_dict, offset=key.offset,
            registry_type=registry_type, urls=self.URLS)
        parser_context.ProduceEvent(event_object, plugin_name=self.NAME)

      else:
        text_dict[value.name] = value.data

    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_timestamp, key.path, text_dict, offset=key.offset,
        registry_type=registry_type, urls=self.URLS)
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)


winreg.WinRegistryParser.RegisterPlugins([
    BootVerificationPlugin, BootExecutePlugin])
