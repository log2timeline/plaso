#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Plug-in to collect information about the Windows timezone settings."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class WinRegTimezonePlugin(interface.KeyPlugin):
  """Plug-in to collect information about the Windows timezone settings."""

  NAME = 'winreg_timezone'
  DESCRIPTION = u'Parser for Windows timezone settings.'

  REG_TYPE = 'SYSTEM'
  REG_KEYS = [u'\\{current_control_set}\\Control\\TimeZoneInformation']
  URLS = []

  WIN_TIMEZONE_VALUE_NAMES = (
      u'ActiveTimeBias', u'Bias', u'DaylightBias', u'DaylightName',
      u'DynamicDaylightTimeDisabled', u'StandardBias', u'StandardName',
      u'TimeZoneKeyName')

  def _GetValue(self, value_name, key):
    """Get value helper, it returns the key value if exists.

    Given the Registry key and the value_name it returns the data in the value
    or None if value_name does not exist.

    Args:
      value_name: the name of the value.
      key: Registry key (instance of winreg.WinRegKey).

    Returns:
      The data inside a Registry value or None.
    """
    value = key.GetValue(value_name)
    if value:
      return value.data

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Collect values and return an event.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    if key is None:
      return
    text_dict = {}
    for value_name in self.WIN_TIMEZONE_VALUE_NAMES:
      text_dict[value_name] = self._GetValue(value_name, key)

    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_timestamp, key.path, text_dict, offset=key.offset,
        registry_type=registry_type)

    parser_mediator.ProduceEvent(event_object)


# Let's register the plugin.
winreg.WinRegistryParser.RegisterPlugin(WinRegTimezonePlugin)
