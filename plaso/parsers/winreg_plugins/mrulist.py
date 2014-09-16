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
"""This file contains a MRUList Registry plugin."""

from plaso.events import windows_events
from plaso.parsers.winreg_plugins import interface


class MRUListPlugin(interface.ValuePlugin):
  """A Registry plugin for keys that contain a MRUList value."""

  NAME = 'winreg_mrulist'

  REG_TYPE = 'any'
  REG_VALUES = frozenset(['MRUList', 'a'])
  URLS = [u'http://forensicartifacts.com/tag/mru/']

  def GetEntries(
      self, parser_context, file_entry=None, key=None, registry_type=None,
      **unused_kwargs):
    """Extracts event objects from a MRU list.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    mru_list_value = key.GetValue('MRUList')
    if not mru_list_value:
      error_string = u'Key: {0:s}, value: MRUList missing.'.format(key.path)
      parser_context.ProduceParseError(
          self.NAME, error_string, file_entry=file_entry)
      return

    timestamp = key.last_written_timestamp

    entry_list = []
    text_dict = {}
    for entry_index, mru_value_name in enumerate(mru_list_value.data):
      value = key.GetValue(mru_value_name)
      if not value:
        error_string = u'Key: {0:s}, value: {1:s} missing.'.format(
            key.path, mru_value_name)
        parser_context.ProduceParseError(
            self.NAME, error_string, file_entry=file_entry)
        continue

      if not value.data:
        error_string = u'Key: {0:s}, value: {1:s} data missing.'.format(
            key.path, mru_value_name)
        parser_context.ProduceParseError(
            self.NAME, error_string, file_entry=file_entry)
        continue

      if not value.DataIsString():
        # TODO: add support for shell item based MRU value data.
        mru_value_string = u''
      else:
        mru_value_string = value.data

      entry_list.append(mru_value_string)
      text_dict[u'Index: {0:d} [MRU Value {1:s}]'.format(
          entry_index + 1, mru_value_name)] = mru_value_string

    event_object = windows_events.WindowsRegistryEvent(
        timestamp, key.path, text_dict, offset=key.offset,
        registry_type=registry_type, urls=self.URLS,
        source_append=': MRU List')
    event_object.mru_list = entry_list
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)
