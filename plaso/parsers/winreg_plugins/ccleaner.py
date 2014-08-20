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
"""Parser for the CCleaner Registry key."""

from plaso.lib import event
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import interface


__author__ = 'Marc Seguin (segumarc@gmail.com)'


class CCleanerPlugin(interface.KeyPlugin):
  """Gathers the CCleaner Keys for NTUSER hive."""

  NAME = 'winreg_ccleaner'

  REG_KEYS = [u'\\Software\\Piriform\\CCleaner']
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'CCleaner Registry key'

  def GetEntries(self, parser_context, key=None, **unused_kwargs):
    """Extracts event objects from a CCleaner Registry key.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: A Windows Registry key (instance of WinRegKey).
    """
    for value in key.GetValues():
      if not value.name or not value.data:
        continue

      text_dict = {}
      text_dict[value.name] = value.data

      if value.name == u'UpdateKey':
        timestamp = timelib.Timestamp.FromTimeString(
            value.data, timezone=parser_context.timezone)
        event_object = event.WinRegistryEvent(key.path, text_dict, timestamp)

      elif value.name == '0':
        event_object = event.WinRegistryEvent(
            key.path, text_dict, key.timestamp)

      else:
        event_object = event.WinRegistryEvent(key.path, text_dict, 0)

      event_object.source_append = u': {0:s}'.format(self.DESCRIPTION)
      parser_context.ProduceEvent(event_object, plugin_name=self.NAME)
