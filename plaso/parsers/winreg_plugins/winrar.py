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

import re

from plaso.lib import event
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class WinRarHistoryPlugin(interface.KeyPlugin):
  """Base class for WinRAR History plugins."""
  # TODO: Create NTUSER.DAT test file with WinRAR data.

  # TODO: Re-enable after we modify the key plugin so that it can define more
  # than a single registry key.
  #NAME = 'winreg_winrar'

  __abstract = True

  DESCRIPTION = 'WinRAR History'

  _RE_VALUE_NAME = re.compile(r'^[0-9]+$', re.I)

  def GetEntries(self):
    """Collect values under WinRAR ArcHistory and return event for each one."""
    for value in self._key.GetValues():
      # Ignore any value not in the form: '[0-9]+'.
      if not value.name or not self._RE_VALUE_NAME.search(value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      if value.name == '0':
        timestamp = self._key.last_written_timestamp
      else:
        timestamp = 0

      text_dict = {}
      text_dict[value.name] = value.data

      # TODO: shouldn't this behavior be, put all the values
      # into a single event object with the last written time of the key?
      yield event.WinRegistryEvent(
          self._key.path, text_dict, timestamp=timestamp,
          source_append=': {0:s}'.format(self.DESCRIPTION))


# TODO: Merge into a single class once key plugins support more than a single
# key.
class WinRarArcHistoryPlugin(WinRarHistoryPlugin):
  """Gathers WinRAR ArcHistory from the User hive."""

  NAME = 'winreg_winrar_1'

  REG_KEY = '\\Software\\WinRAR\\ArcHistory'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'WinRAR Archive History'


class WinRarArcNamePlugin(WinRarHistoryPlugin):
  """Gathers WinRAR ArcName from the User hive."""

  NAME = 'winreg_winrar_2'

  REG_KEY = '\\Software\\WinRAR\\DialogEditHistory\\ArcName'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'WinRAR Archive Name'


class WinRarExtrPathPlugin(WinRarHistoryPlugin):
  """Gathers WinRAR ExtrPath from the User hive."""

  NAME = 'winreg_winrar_3'

  REG_KEY = '\\Software\\WinRAR\\DialogEditHistory\\ExtrPath'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'WinRAR Extraction Path'
