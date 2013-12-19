#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a parser for CCleaner for Plaso."""
from plaso.lib import event
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import interface

import pytz


__author__ = 'Marc Seguin (segumarc@gmail.com)'


class CCleanerPlugin(interface.KeyPlugin):
  """Gathers the CCleaner Keys for NTUSER hive."""

  NAME = 'winreg_ccleaner'

  REG_KEY = '\\Software\\Piriform\\CCleaner'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'CCleaner Registry key'

  def GetEntries(self):
    """Collect values under CCleaner and return event for each one."""
    for value in self._key.GetValues():
      if not value.name:
        continue
      text_dict = {}
      text_dict[value.name] = value.data
      if not text_dict[value.name]:
        continue

      if value.name == 'UpdateKey':
        zone = getattr(self._config, 'timezone', pytz.utc)
        update_key = self._key.GetValue('UpdateKey')
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict,
            timelib.Timestamp.FromTimeString(update_key.data,zone))
      elif value.name == '0':
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict, self._key.timestamp)
      else:
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict, 0)

      reg_evt.source_append = ': {}'.format(self.DESCRIPTION)
      yield reg_evt
