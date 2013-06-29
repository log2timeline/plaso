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
"""This file contains a parser for WinRAR for Plaso."""


from plaso.lib import event
from plaso.lib import win_registry_interface


__author__ = 'David Nides (david.nides@gmail.com)'


class WinRAR(win_registry_interface.KeyPlugin):
  """Base class for WinRAR History plugins."""
  # TODO: Create NTUSER.DAT test file with WinRAR data.

  __abstract = True

  DESCRIPTION = 'WinRAR History'

  def GetEntries(self):
    """Collect values under WinRAR ArcHistory and return event for each one."""
    for value in self._key.GetValues():
      if not value.name:
        continue
      text_dict = {}
      text_dict[value.name] = value.GetStringData()
      if not text_dict[value.name]:
        continue

      if value.name == '0':
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict, self._key.timestamp)
      else:
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict, 0)

      reg_evt.source_append = ': {}'.format(self.DESCRIPTION)
      yield reg_evt


class WinRARArcHistory(WinRAR):
  """Gathers WinRAR ArcHistory from the NTUSER hive."""

  REG_KEY = '\\Software\\WinRAR\\ArcHistory'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = "WinRAR Archive History"


class WinRARArcName(WinRAR):
  """Gathers WinRAR ArcName from the NTUSER hive."""

  REG_KEY = '\\Software\\WinRAR\\DialogEditHistory\\ArcName'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = "WinRAR Archive Name"


class WinRARExtrPath(WinRAR):
  """Gathers WinRAR ExtrPath from the NTUSER hive."""

  REG_KEY = '\\Software\\WinRAR\\DialogEditHistory\\ExtrPath'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = "WinRAR Extraction Path"
